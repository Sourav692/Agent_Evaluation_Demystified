"""Governance for a shared evaluation platform: tenants, roles, a versioned registry, redaction,
a hash-chained audit log and per-team cost attribution. Week 14 builds it; Week 16 reuses it.

Every public method of `Platform` takes the caller's principal ID and nothing else about who the
caller is. The platform looks up the tenant and the role itself, decides in `_authorize`, writes
an audit event for the decision whether it allowed or denied, and charges eval runs to the
caller's tenant. Callers cannot pass a tenant, so they cannot claim someone else's.

Public API:
    Platform(policy, db=":memory:", clock=None, runners=None, names=())
        .principal(actor) -> Principal | None
        .register_dataset(actor, name, records) -> ref        "tenant/name@vN"
        .read_dataset(actor, ref) -> list[dict]
        .register_evaluator(actor, name, spec) -> ref
        .read_evaluator(actor, ref) -> dict
        .share_evaluator(actor, ref, grantee_tenant) -> None
        .run_eval(actor, dataset_ref, evaluator_refs, **runner_args) -> dict   (the run record)
        .read_run(actor, run_id) -> dict
        .usage(actor) -> list[dict]                            per-tenant attribution
        .audit(actor) -> list[dict]                            events the caller may see
        .audit_head() -> (seq, hash)                           an anchor to store outside the DB
        .verify_audit(anchor=None) -> list[str]                empty means the chain is intact
    evaluate_rules(spec, metrics) -> {"verdict", "rules"}      missing metrics fail closed
    redact_records(records, names=()) -> list[dict]
    sha256_json(obj) -> str
    Denied, IntegrityError, PUBLIC_DENIAL
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from shared.tracing import redact_text

GENESIS = "0" * 64
TEXT_FIELDS = ("message", "query", "note", "reply", "text")   # free text: redacted before storage
PUBLIC_DENIAL = "not found or not permitted"                  # same words for missing and forbidden
SALT = "week-14"                                              # customer-ID pseudonyms; rotate per deployment
REF = re.compile(r"^(?:(?P<tenant>[a-z0-9-]+)/)?(?P<name>[a-z0-9-]+)(?:@v(?P<version>\d+))?$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
    kind TEXT, tenant TEXT, name TEXT, version INTEGER, sha256 TEXT, body TEXT,
    created_by TEXT, created_at TEXT, PRIMARY KEY (kind, tenant, name, version));
CREATE TRIGGER IF NOT EXISTS artifacts_no_update BEFORE UPDATE ON artifacts
    BEGIN SELECT RAISE(ABORT, 'registry entries are immutable: register a new version'); END;
CREATE TRIGGER IF NOT EXISTS artifacts_no_delete BEFORE DELETE ON artifacts
    BEGIN SELECT RAISE(ABORT, 'registry entries are immutable: register a new version'); END;
CREATE TABLE IF NOT EXISTS grants (tenant TEXT, name TEXT, grantee TEXT, PRIMARY KEY (tenant, name, grantee));
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, tenant TEXT, body TEXT);
CREATE TABLE IF NOT EXISTS usage (run_id TEXT, tenant TEXT, actor TEXT, cases INTEGER, cost_usd REAL);
CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, event TEXT, prev TEXT, hash TEXT);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
    BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
    BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
"""


class Denied(Exception):
    """The caller may not do this. The message is safe to show; the audit event holds the reason."""


class IntegrityError(Exception):
    """A stored entry no longer matches its recorded hash."""


@dataclass(frozen=True)
class Principal:
    id: str
    tenant: str          # "*" for platform roles such as the auditor
    role: str


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha256_json(obj) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def redact_records(records: list[dict], names: tuple[str, ...] = (), salt: str = SALT) -> list[dict]:
    """Mask emails, card numbers and known names in free-text fields; pseudonymize customer IDs in them.
    Structured fields (customer_id, target_order) are left alone: the runner needs them to replay a case."""
    return [{k: redact_text(v, names, salt) if k in TEXT_FIELDS and isinstance(v, str) else v
             for k, v in record.items()} for record in records]


def evaluate_rules(spec: dict, metrics: dict) -> dict:
    """Apply an evaluator's rules to a run's metrics. A metric the run did not produce fails the rule."""
    results = []
    for rule in spec["rules"]:
        value = metrics.get(rule["metric"])
        if value is None:
            status = "MISSING"
        else:
            ok = value <= rule["limit"] if rule["op"] == "<=" else value >= rule["limit"]
            status = "PASS" if ok else "FAIL"
        results.append({**rule, "value": value, "status": status})
    return {"verdict": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL", "rules": results}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Platform:
    """The evaluation API. Permissions live here, in the backend, not in the callers."""

    def __init__(self, policy: dict, db: str = ":memory:", clock=None, runners: dict | None = None,
                 names: tuple[str, ...] = ()):
        self.policy = policy
        self.db = sqlite3.connect(db)
        self.db.executescript(SCHEMA)
        self.clock = clock or utc_now
        self.runners = runners or {}
        self.names = tuple(names)

    # --- Identity and the one place access is decided -----------------------------------------------

    def principal(self, actor: str) -> Principal | None:
        entry = self.policy["principals"].get(actor)
        return Principal(actor, entry["tenant"], entry["role"]) if entry else None

    def _authorize(self, actor: str, action: str, resource: str, owner: str | None) -> Principal:
        """Allow or deny `action` on `resource`, owned by tenant `owner` (None: it does not exist)."""
        p = self.principal(actor)
        if p is None:
            reason = "unknown_principal"
        elif action not in self.policy["roles"][p.role]:
            reason = "role"
        elif owner is None:
            reason = "missing"
        elif p.tenant not in ("*", owner) and not self._granted(resource, p.tenant, action):
            reason = "cross_tenant"
        else:
            self._audit(actor, p, action, resource, owner, "allow")
            return p
        self._audit(actor, p, action, resource, owner, "deny", reason)
        if reason == "role":
            raise Denied(f"{action} is not permitted for role {p.role}")
        raise Denied(PUBLIC_DENIAL)                    # missing and cross-tenant look the same

    def _granted(self, resource: str, tenant: str, action: str) -> bool:
        if action != "evaluator.read" or not resource.startswith("evaluator:"):
            return False
        owner, name = resource.split(":", 1)[1].split("@")[0].split("/")
        return self.db.execute("SELECT 1 FROM grants WHERE tenant=? AND name=? AND grantee=?",
                               (owner, name, tenant)).fetchone() is not None

    # --- Audit: append-only, hash-chained -----------------------------------------------------------

    def _audit(self, actor, p, action, resource, owner, decision, reason="", detail=""):
        event = {"at": self.clock(), "actor": redact_text(actor, self.names, SALT), "tenant": p.tenant if p else None,
                 "action": action, "resource": resource, "owner": owner, "decision": decision,
                 "reason": reason, "detail": redact_text(detail, self.names, SALT)}
        seq, prev = self.audit_head()
        digest = hashlib.sha256(prev.encode() + canonical(event)).hexdigest()
        self.db.execute("INSERT INTO audit VALUES (?, ?, ?, ?)", (seq + 1, json.dumps(event), prev, digest))
        self.db.commit()

    def audit_head(self) -> tuple[int, str]:
        row = self.db.execute("SELECT seq, hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        return (row[0], row[1]) if row else (0, GENESIS)

    def verify_audit(self, anchor: tuple[int, str] | None = None) -> list[str]:
        """Recompute the chain. An anchor (seq, hash) kept outside the database also catches a rewrite."""
        problems, prev, expected_seq = [], GENESIS, 1
        rows = self.db.execute("SELECT seq, event, prev, hash FROM audit ORDER BY seq").fetchall()
        for seq, event, stored_prev, digest in rows:
            if seq != expected_seq:
                problems.append(f"seq {seq}: expected seq {expected_seq}, events are missing")
            if stored_prev != prev:
                problems.append(f"seq {seq}: prev does not match the hash before it")
            if hashlib.sha256(stored_prev.encode() + canonical(json.loads(event))).hexdigest() != digest:
                problems.append(f"seq {seq}: hash does not match the event")
            prev, expected_seq = digest, seq + 1
        if anchor is not None:
            found = dict((seq, digest) for seq, _e, _p, digest in rows).get(anchor[0])
            if found != anchor[1]:
                problems.append(f"anchor seq {anchor[0]}: hash differs from the one stored outside the database")
        return problems

    def audit(self, actor: str) -> list[dict]:
        p = self._authorize(actor, "audit.read", "audit", self._own(actor))
        events = [{"seq": seq, **json.loads(e)} for seq, e in self.db.execute("SELECT seq, event FROM audit ORDER BY seq")]
        return events if p.tenant == "*" else [e for e in events if p.tenant in (e["tenant"], e["owner"])]

    def _own(self, actor: str) -> str | None:
        p = self.principal(actor)
        return p.tenant if p else None

    # --- Registry: datasets and evaluators, immutable and versioned ---------------------------------

    def _resolve(self, kind: str, ref: str, actor: str) -> tuple[str, str | None, dict | None]:
        """Turn a ref into (canonical resource name, owner tenant or None, row). Never checks access."""
        m = REF.match(ref)
        tenant = (m and m["tenant"]) or self._own(actor) or "?"
        if not m:
            return f"{kind}:{ref}", None, None
        sql = "SELECT version, sha256, body FROM artifacts WHERE kind=? AND tenant=? AND name=?"
        args = [kind, tenant, m["name"]]
        if m["version"]:
            sql, args = sql + " AND version=?", args + [int(m["version"])]
        row = self.db.execute(sql + " ORDER BY version DESC LIMIT 1", args).fetchone()
        if row is None:
            return f"{kind}:{tenant}/{m['name']}", None, None
        version, digest, body = row
        name = f"{tenant}/{m['name']}@v{version}"
        return f"{kind}:{name}", tenant, {"ref": name, "version": version, "sha256": digest, "body": body}

    def _register(self, kind: str, actor: str, name: str, body) -> str:
        p = self._authorize(actor, f"{kind}.write", f"{kind}:{self._own(actor)}/{name}", self._own(actor))
        digest = sha256_json(body)
        _res, _owner, latest = self._resolve(kind, f"{p.tenant}/{name}", actor)
        if latest and latest["sha256"] == digest:      # same content: same version, nothing new stored
            return latest["ref"]
        version = latest["version"] + 1 if latest else 1
        self.db.execute("INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (kind, p.tenant, name, version, digest, json.dumps(body), actor, self.clock()))
        self.db.commit()
        ref = f"{p.tenant}/{name}@v{version}"
        self._audit(actor, p, f"{kind}.registered", f"{kind}:{ref}", p.tenant, "allow", detail=f"sha256 {digest[:12]}")
        return ref

    def _read(self, kind: str, actor: str, ref: str) -> tuple[dict, object]:
        resource, owner, row = self._resolve(kind, ref, actor)
        p = self._authorize(actor, f"{kind}.read", resource, owner)
        body = json.loads(row["body"])
        if sha256_json(body) != row["sha256"]:
            self._audit(actor, p, f"{kind}.read", resource, owner, "error", "integrity")
            raise IntegrityError(f"{row['ref']} does not match its recorded sha256 {row['sha256'][:12]}")
        return row, body

    def register_dataset(self, actor: str, name: str, records: list[dict]) -> str:
        return self._register("dataset", actor, name, redact_records(records, self.names))

    def read_dataset(self, actor: str, ref: str) -> list[dict]:
        return self._read("dataset", actor, ref)[1]

    def register_evaluator(self, actor: str, name: str, spec: dict) -> str:
        return self._register("evaluator", actor, name, spec)

    def read_evaluator(self, actor: str, ref: str) -> dict:
        return self._read("evaluator", actor, ref)[1]

    def share_evaluator(self, actor: str, ref: str, grantee: str) -> None:
        resource, owner, row = self._resolve("evaluator", ref, actor)
        self._authorize(actor, "evaluator.share", resource, owner)
        tenant, name = row["ref"].split("@")[0].split("/")
        self.db.execute("INSERT OR IGNORE INTO grants VALUES (?, ?, ?)", (tenant, name, grantee))
        self.db.commit()

    # --- Runs, budgets and attribution --------------------------------------------------------------

    def spent(self, tenant: str) -> float:
        return self.db.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM usage WHERE tenant=?", (tenant,)).fetchone()[0]

    def run_eval(self, actor: str, dataset_ref: str, evaluator_refs: list[str], **runner_args) -> dict:
        """Run the caller's tenant's runner on a pinned dataset, apply evaluators, charge the caller's tenant."""
        tenant = self._own(actor)
        p = self._authorize(actor, "eval.run", f"tenant:{tenant}", tenant)
        dataset_row, records = self._read("dataset", actor, dataset_ref)
        evaluators = [self._read("evaluator", actor, ref) for ref in evaluator_refs]
        config = self.policy["tenants"][tenant]
        estimate = len(records) * config["reserve_per_case_usd"]
        if self.spent(tenant) + estimate > config["monthly_budget_usd"] + 1e-9:
            self._audit(actor, p, "eval.admit", f"tenant:{tenant}", tenant, "deny", "budget",
                        f"spent {self.spent(tenant):.4f} + estimate {estimate:.4f} > {config['monthly_budget_usd']}")
            raise Denied(f"budget exceeded for {tenant}")
        result = self.runners[config["runner"]](records, **runner_args)
        run_id = f"run-{self.db.execute('SELECT COUNT(*) FROM runs').fetchone()[0] + 1:04d}"
        body = {"run_id": run_id, "tenant": tenant, "actor": actor, "at": self.clock(),
                "runner": config["runner"], "runner_args": runner_args,
                "dataset": {"ref": dataset_row["ref"], "sha256": dataset_row["sha256"]},
                "evaluators": [{"ref": row["ref"], "sha256": row["sha256"], **evaluate_rules(spec, result["metrics"])}
                               for row, spec in evaluators],
                "metrics": result["metrics"], "cost_usd": round(result["cost_usd"], 6)}
        self.db.execute("INSERT INTO runs VALUES (?, ?, ?)", (run_id, tenant, json.dumps(body)))
        self.db.execute("INSERT INTO usage VALUES (?, ?, ?, ?, ?)", (run_id, tenant, actor, len(records), body["cost_usd"]))
        self.db.commit()
        self._audit(actor, p, "eval.completed", f"run:{run_id}", tenant, "allow", detail=f"cost {body['cost_usd']:.4f}")
        return body

    def read_run(self, actor: str, run_id: str) -> dict:
        row = self.db.execute("SELECT tenant, body FROM runs WHERE run_id=?", (run_id,)).fetchone()
        self._authorize(actor, "run.read", f"run:{run_id}", row[0] if row else None)
        return json.loads(row[1])

    def usage(self, actor: str) -> list[dict]:
        p = self._authorize(actor, "usage.read", "usage", self._own(actor))
        rows = []
        for tenant, config in self.policy["tenants"].items():
            if p.tenant not in ("*", tenant):
                continue
            runs, cases, cost = self.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(cases), 0), COALESCE(SUM(cost_usd), 0) FROM usage WHERE tenant=?",
                (tenant,)).fetchone()
            rows.append({"tenant": tenant, "runs": runs, "cases": cases, "cost_usd": round(cost, 6),
                         "budget_usd": config["monthly_budget_usd"],
                         "remaining_usd": round(config["monthly_budget_usd"] - cost, 6)})
        return rows
