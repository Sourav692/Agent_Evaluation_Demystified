"""Week 14 lab: one evaluation platform shared by three fictional teams.

The platform is `shared/governance.py`. This lab gives it the teams' runners (Week 4's retrieval
benchmark and Week 11's tool and fault suites, loaded by path and unchanged), registers each team's
datasets and evaluators, runs a short scripted day of work, and then attacks it: cross-tenant
probes, an edit to a registered dataset, personal data in an upload, and a rewritten audit log.

Usage, from new_course/:
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py demo
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py access
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py probe
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py registry
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py redaction
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py audit
    python3 weeks/week-14-multi-tenant-governance/handson/lab.py usage

Everything is local and free. Teams, people, budgets and costs are fictional or SIMULATED.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
DATA = HERE.parent / "dataset"
RUNS = HERE / "runs" / "week-14"
sys.path.insert(0, str(COURSE))

from shared.governance import (  # noqa: E402
    GENESIS, PUBLIC_DENIAL, Denied, IntegrityError, Platform, canonical, redact_records,
)
from shared.support_agent import load_world  # noqa: E402
from shared.tracing import CARD_NUMBER, CUSTOMER_ID, EMAIL  # noqa: E402

TENANTS = json.loads((DATA / "tenants-v1.json").read_text())
EVALUATORS = json.loads((DATA / "evaluators-v1.json").read_text())
NAMES = tuple(c["name"] for c in load_world()["customers"].values())
RETRIEVAL_COST_PER_QUERY = 0.0002          # SIMULATED: priced like one embedding call per query


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_week_lab(folder: str, name: str):
    """Earlier weeks' labs run unchanged, loaded by path (Week 11's pattern)."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W4 = load_week_lab("week-04-retrieval-evaluation", "week04_lab_for_w14")
W11 = load_week_lab("week-11-evaluation-harness-and-ci", "week11_lab_for_w14")


# --- The three teams' runners: each returns metrics and a SIMULATED cost --------------------------

def run_retrieval(records: list[dict], retriever: str = "hybrid", k: int = 5) -> dict:
    rows = W4.run_benchmark(retriever, k, queries=records)
    return {"metrics": {"cases": len(rows), "recall_at_5": round(W4.mean(rows, "recall"), 4),
                        "ndcg_at_5": round(W4.mean(rows, "ndcg"), 4),
                        "stale_or_restricted_hits": sum(r["violations"] for r in rows)},
            "cost_usd": len(rows) * RETRIEVAL_COST_PER_QUERY}


def suite_metrics(artifact: dict) -> dict:
    summary = artifact["summary"]
    return {"cases": artifact["completed_cases"],
            "pass_rate": round(summary["status"]["pass"] / artifact["completed_cases"], 4),
            **summary["safety"]}


def run_tools(records: list[dict], agent: str = "v2", strict: bool = True) -> dict:
    artifact = W11.run_suite("tools", agent, strict, cases=records)
    return {"metrics": suite_metrics(artifact), "cost_usd": artifact["summary"]["cost_usd"]}


def run_faults(records: list[dict], agent: str = "stable_key", strict: bool = False) -> dict:
    """Trust and safety runs the fault suite as a safety probe: on the lax backend (Week 12)."""
    artifact = W11.run_suite("faults", agent, strict, cases=records)
    return {"metrics": suite_metrics(artifact), "cost_usd": artifact["summary"]["cost_usd"]}


RUNNERS = {"retrieval": run_retrieval, "tools": run_tools, "faults": run_faults}


# --- Building the platform and a scripted day of work ---------------------------------------------

class SimClock:
    """SIMULATED wall clock: every reading is one minute after the last, from 2026-03-16 09:00 UTC."""

    def __init__(self, start: str = "2026-03-16T09:00:00+00:00"):
        self.t = datetime.fromisoformat(start)

    def __call__(self) -> str:
        now, self.t = self.t, self.t + timedelta(minutes=1)
        return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_platform(db: str = ":memory:") -> Platform:
    return Platform(TENANTS, db=db, clock=SimClock(), runners=RUNNERS, names=NAMES)


def seed(platform: Platform) -> dict:
    """Each team registers its datasets and evaluators; trust-safety shares refund-safety."""
    refs = {
        "policy-queries": platform.register_dataset(
            "rag.engineer", "policy-queries", read_jsonl(COURSE / "datasets/retrieval/policy-queries-v1.jsonl")),
        "escalation-queries": platform.register_dataset(
            "rag.engineer", "escalation-queries", read_jsonl(DATA / "escalation-queries-v1.jsonl")),
        "tool-cases": platform.register_dataset(
            "refunds.engineer", "tool-cases", read_jsonl(COURSE / "datasets/tools/tool-cases-v1.jsonl")),
        "fault-cases": platform.register_dataset(
            "safety.engineer", "fault-cases", read_jsonl(COURSE / "datasets/faults/fault-cases-v1.jsonl")),
    }
    for entry in EVALUATORS["evaluators"]:
        refs[entry["name"]] = platform.register_evaluator(entry["owner"], entry["name"], entry["spec"])
        for grantee in entry["share_with"]:
            platform.share_evaluator(entry["owner"], refs[entry["name"]], grantee)
    return refs


SCRIPT = [  # (actor, dataset, evaluators, runner arguments): one SIMULATED working day
    ("rag.engineer", "policy-queries", ["retrieval-quality"], {}),
    ("rag.engineer", "escalation-queries", ["retrieval-quality"], {}),
    ("refunds.engineer", "tool-cases", ["task-success", "refund-safety"], {"agent": "v1"}),
    ("refunds.engineer", "tool-cases", ["task-success", "refund-safety"], {"agent": "v2"}),
    ("safety.engineer", "fault-cases", ["refund-safety"], {"agent": "naive_retry"}),
    ("safety.engineer", "fault-cases", ["refund-safety"], {"agent": "stable_key"}),
    ("refunds.engineer", "tool-cases", ["task-success", "refund-safety"], {"agent": "v2", "strict": False}),
]


def run_script(platform: Platform, refs: dict) -> list[dict]:
    """Run SCRIPT. A denied run is recorded as {"denied": message} so the day's story stays complete."""
    out = []
    for actor, dataset, evaluators, args in SCRIPT:
        try:
            out.append(platform.run_eval(actor, refs[dataset], [refs[e] for e in evaluators], **args))
        except Denied as exc:
            out.append({"actor": actor, "dataset": refs[dataset], "runner_args": args, "denied": str(exc)})
    return out


def build_day(db: str = ":memory:") -> tuple[Platform, dict, list[dict]]:
    platform = build_platform(db)
    refs = seed(platform)
    return platform, refs, run_script(platform, refs)


# --- Access: every principal against the same calls ------------------------------------------------

def access_matrix(platform: Platform, refs: dict, runs: list[dict]) -> dict:
    """Call the API as every principal. Own-tenant targets come from the caller's tenant."""
    first_run = {r["tenant"]: r["run_id"] for r in reversed(runs) if "run_id" in r}
    own_dataset = {"support-rag": refs["policy-queries"], "refunds-agent": refs["tool-cases"],
                   "trust-safety": refs["fault-cases"]}
    own_evaluator = {"support-rag": "retrieval-quality", "refunds-agent": "task-success",
                     "trust-safety": "refund-safety"}
    other = {"support-rag": "refunds-agent", "refunds-agent": "support-rag", "trust-safety": "support-rag"}
    spec = {e["name"]: e["spec"] for e in EVALUATORS["evaluators"]}
    matrix = {}
    for actor, entry in TENANTS["principals"].items():
        t = entry["tenant"] if entry["tenant"] != "*" else "support-rag"
        calls = {
            "read own dataset": lambda: platform.read_dataset(actor, own_dataset[t]),
            "write dataset": lambda: platform.register_dataset(actor, "scratch", [{"note": "access check"}]),
            "write evaluator": lambda: platform.register_evaluator(actor, own_evaluator[t], spec[own_evaluator[t]]),
            "read own run": lambda: platform.read_run(actor, first_run[t]),
            "read other team's dataset": lambda: platform.read_dataset(actor, own_dataset[other[t]]),
            "read other team's run": lambda: platform.read_run(actor, first_run[other[t]]),
            "use refund-safety": lambda: platform.read_evaluator(actor, refs["refund-safety"]),
            "read usage": lambda: platform.usage(actor),
            "read audit": lambda: platform.audit(actor),
        }
        row = {}
        for label, call in calls.items():
            try:
                call()
                row[label] = "allow"
            except Denied:
                row[label] = "deny"
        matrix[actor] = row
    return matrix


# --- Probing another tenant -------------------------------------------------------------------------

PROBES = [  # what refunds.engineer tries against support-rag and trust-safety
    ("read_dataset", "support-rag/escalation-queries@v1"),
    ("read_dataset", "support-rag/escalation-queries"),
    ("read_dataset", "support-rag/no-such-dataset@v1"),
    ("read_dataset", "trust-safety/fault-cases@v1"),
    ("read_run", "run-0001"),
    ("read_run", "run-0099"),
    ("read_evaluator", "support-rag/retrieval-quality@v1"),
    ("register_evaluator", "refund-safety"),
]


def probe(platform: Platform, actor: str = "refunds.engineer") -> list[tuple[str, str, str]]:
    """Each probe's public answer. Every one is denied, and missing and forbidden read the same."""
    out = []
    for method, target in PROBES:
        try:
            if method == "register_evaluator":
                platform.register_evaluator(actor, target, {"rules": []})
            else:
                getattr(platform, method)(actor, target)
            out.append((method, target, "ALLOWED"))
        except Denied as exc:
            out.append((method, target, str(exc)))
    return out


def read_run_trusting_caller(platform: Platform, actor: str, tenant: str, run_id: str) -> dict:
    """DRILL 1, broken on purpose: the caller says which tenant it acts for, and the code believes it."""
    row = platform.db.execute("SELECT tenant, body FROM runs WHERE run_id=?", (run_id,)).fetchone()
    p = platform.principal(actor)
    if p is None or "run.read" not in TENANTS["roles"][p.role] or row is None or row[0] != tenant:
        raise Denied(PUBLIC_DENIAL)
    return json.loads(row[1])


# --- Registry: versions, the database trigger and the hash check -----------------------------------

def registry_story(platform: Platform) -> list[str]:
    """Register, re-register, change, try to edit in place, then tamper behind the API's back."""
    lines = []
    cases = read_jsonl(COURSE / "datasets/tools/tool-cases-v1.jsonl")
    lines.append(f"register tool-cases                  -> {platform.register_dataset('refunds.engineer', 'tool-cases', cases)}")
    lines.append(f"register the same 30 cases again     -> {platform.register_dataset('refunds.engineer', 'tool-cases', cases)}")
    changed = [dict(c, risk="critical") if c["case_id"] == "t-023" else c for c in cases]
    lines.append(f"register with t-023 risk changed     -> {platform.register_dataset('refunds.engineer', 'tool-cases', changed)}")
    v1 = platform.read_dataset("refunds.engineer", "tool-cases@v1")
    lines.append(f"read tool-cases@v1, t-023 risk       -> {next(c['risk'] for c in v1 if c['case_id'] == 't-023')}")
    try:
        platform.db.execute("UPDATE artifacts SET body = '[]' WHERE name = 'tool-cases' AND version = 1")
    except sqlite3.DatabaseError as exc:
        lines.append(f"UPDATE tool-cases v1 in the database -> refused: {exc}")
    platform.db.execute("DROP TRIGGER artifacts_no_update")          # someone with database access
    platform.db.execute("UPDATE artifacts SET body = ? WHERE name = 'tool-cases' AND version = 1",
                        (json.dumps(cases[:29]),))
    try:
        platform.read_dataset("refunds.engineer", "tool-cases@v1")
    except IntegrityError as exc:
        lines.append(f"read after a direct edit             -> refused: {exc}")
    return lines


# --- Redaction: what reaches the database ------------------------------------------------------------

def count_personal_data(text: str) -> dict:
    return {"emails": len(EMAIL.findall(text)), "card numbers": len(CARD_NUMBER.findall(text)),
            "customer IDs": len(CUSTOMER_ID.findall(text)), "names": sum(text.count(n) for n in NAMES)}


def redaction_report(db_path: Path) -> dict:
    """Count personal data in the raw upload, in a pattern-only redaction, and in the database file's bytes."""
    raw = read_jsonl(DATA / "escalation-queries-v1.jsonl")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    platform, _refs, _runs = build_day(str(db_path))
    platform.db.close()
    stored = db_path.read_bytes().decode("utf-8", errors="ignore")
    return {"raw upload": count_personal_data(json.dumps(raw)),
            "patterns only": count_personal_data(json.dumps(redact_records(raw))),
            "database file": count_personal_data(stored),
            "customer_id fields": len(re.findall(r'"customer_id": "cust-\d+"', stored)),
            "recall raw": run_retrieval(raw)["metrics"]["recall_at_5"],
            "recall redacted": run_retrieval(redact_records(raw, NAMES))["metrics"]["recall_at_5"]}


# --- Audit: reading it, and two ways to tamper with it -----------------------------------------------

def audit_summary(events: list[dict]) -> Counter:
    return Counter((e["decision"], e["reason"]) for e in events)


def delete_event(platform: Platform, seq: int) -> None:
    """Tamper 1: remove one event, as someone with direct database access."""
    platform.db.execute("DROP TRIGGER IF EXISTS audit_no_delete")
    platform.db.execute("DELETE FROM audit WHERE seq = ?", (seq,))


def rewrite_chain(platform: Platform) -> None:
    """Tamper 2: renumber the remaining events and recompute every hash, so the chain verifies again."""
    platform.db.execute("DROP TRIGGER IF EXISTS audit_no_update")
    rows = platform.db.execute("SELECT seq, event FROM audit ORDER BY seq").fetchall()
    platform.db.execute("DELETE FROM audit")
    prev = GENESIS
    for new_seq, (_seq, event) in enumerate(rows, start=1):
        digest = hashlib.sha256(prev.encode() + canonical(json.loads(event))).hexdigest()
        platform.db.execute("INSERT INTO audit VALUES (?, ?, ?, ?)", (new_seq, event, prev, digest))
        prev = digest


# --- Printing ----------------------------------------------------------------------------------------

def print_demo(refs: dict, runs: list[dict]) -> None:
    print("Registered (SIMULATED platform, fictional teams):")
    for ref in refs.values():
        print(f"  {ref}")
    print(f"{'run':9} {'actor':17} {'dataset':34} {'args':30} {'verdicts':38} cost $")
    for r in runs:
        args = json.dumps(r["runner_args"], separators=(",", ":"))
        if "denied" in r:
            print(f"{'-':9} {r['actor']:17} {r['dataset']:34} {args:30} DENIED: {r['denied']}")
            continue
        verdicts = ", ".join(f"{e['ref'].split('/')[1].split('@')[0]} {e['verdict']}" for e in r["evaluators"])
        print(f"{r['run_id']:9} {r['actor']:17} {r['dataset']['ref']:34} {args:30} {verdicts:38} {r['cost_usd']:.4f}")


def print_matrix(matrix: dict) -> None:
    labels = list(next(iter(matrix.values())))
    print(f"{'principal':17} " + " ".join(f"{i + 1:>3}" for i in range(len(labels))))
    for actor, row in matrix.items():
        print(f"{actor:17} " + " ".join(f"{'yes' if row[l] == 'allow' else ' - ':>3}" for l in labels))
    for i, label in enumerate(labels, 1):
        print(f"  {i}. {label}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["demo", "access", "probe", "registry", "redaction", "audit", "usage"])
    args = parser.parse_args(argv)
    if args.command == "redaction":
        report = redaction_report(RUNS / "platform.db")
        print(f"{'where':16} {'emails':>7} {'card numbers':>13} {'customer IDs':>13} {'names':>6}")
        for where in ("raw upload", "patterns only", "database file"):
            c = report[where]
            print(f"{where:16} {c['emails']:>7} {c['card numbers']:>13} {c['customer IDs']:>13} {c['names']:>6}")
        print(f"customer IDs in the database file: {report['database file']['customer IDs']}, "
              f"{report['customer_id fields']} of them in the structured customer_id field the runner replays")
        print(f"escalation-queries recall@5: raw {report['recall raw']}, as stored {report['recall redacted']}")
        print(f"wrote {(RUNS / 'platform.db').relative_to(COURSE)}")
        return 0
    platform, refs, runs = build_day()
    if args.command == "demo":
        print_demo(refs, runs)
    elif args.command == "access":
        print_matrix(access_matrix(platform, refs, runs))
    elif args.command == "probe":
        for method, target, answer in probe(platform):
            print(f"refunds.engineer {method:18} {target:36} -> {answer}")
        seen = [e for e in platform.audit("rag.owner") if e["decision"] == "deny"]
        print(f"rag.owner's audit view: {len(seen)} denied events on support-rag resources")
        for e in seen:
            print(f"  seq {e['seq']:>3} {e['at']} {e['actor']} {e['action']} {e['resource']} reason={e['reason']}")
    elif args.command == "registry":
        print("\n".join(registry_story(platform)))
    elif args.command == "audit":
        anchor = platform.audit_head()
        print(f"end of day: head seq {anchor[0]}, hash {anchor[1][:16]}..., kept outside the database as the anchor")
        events = platform.audit("platform.auditor")
        print(f"platform.auditor reads {len(events)} events (the read itself is event {anchor[0] + 1}):")
        for (decision, reason), n in sorted(audit_summary(events).items()):
            print(f"  {decision:6} {reason or '-':18} {n}")
        print(f"verify: {platform.verify_audit(anchor) or 'chain intact'}")
        denied = next(e["seq"] for e in events if e["decision"] == "deny")
        delete_event(platform, denied)
        print(f"after deleting seq {denied}: {platform.verify_audit(anchor)[:2]}")
        rewrite_chain(platform)
        print(f"after rewriting the chain, without the anchor: {platform.verify_audit() or 'chain intact'}")
        print(f"after rewriting the chain, with the anchor:    {platform.verify_audit(anchor)}")
        fresh, _refs, _runs = build_day()
        delete_event(fresh, anchor[0])
        print(f"a fresh day with only its newest event, seq {anchor[0]}, deleted: "
              f"without the anchor {fresh.verify_audit() or 'chain intact'}, with it {fresh.verify_audit(anchor)}")
    elif args.command == "usage":
        print(f"{'tenant':14} {'runs':>4} {'cases':>5} {'cost $':>8} {'budget $':>9} {'left $':>8}")
        for u in platform.usage("platform.auditor"):
            print(f"{u['tenant']:14} {u['runs']:>4} {u['cases']:>5} {u['cost_usd']:>8.4f} {u['budget_usd']:>9.2f} "
                  f"{u['remaining_usd']:>8.4f}")
        for e in platform.audit("platform.auditor"):
            if e["reason"] == "budget":
                print(f"denied: {e['actor']} {e['action']} at {e['at']}: {e['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
