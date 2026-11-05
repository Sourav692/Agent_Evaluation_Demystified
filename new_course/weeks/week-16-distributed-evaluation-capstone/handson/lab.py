"""Week 16 lab: a multi-tenant evaluation queue with workers, leases, budgets and a release decision.

The queue is a SQLite table. Submissions go through Week 14's platform (identity, roles, the
dataset registry, budgets, the audit log) and are split into shard jobs. Workers lease jobs,
run them with Week 11's runner (Week 12's candidates registered) or Week 4's retrieval
benchmark, and report back. A lease that expires puts the job back in the queue. Completion is
fenced by the lease token and charges the tenant once, in the same transaction. When every
shard of a release request is finished, the shards are merged into Week 11 artifacts and
Week 12's gate decides. Every request is one Week 13 trace.

Usage, from new_course/:
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py demo
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py compare
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py faults
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py audit
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py dashboard
    python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py threads

`demo`, `compare`, `faults`, `audit` and `dashboard` replay a SIMULATED day on a simulated
clock, so their numbers are the same on every run. `threads` runs real threads against a
SQLite file and reports wall-clock numbers measured on this machine: prototype measurements,
not production capacity. No model is called anywhere in this lab.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import math
import sqlite3
import sys
import threading
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
DATA = HERE.parent / "dataset"
RUNS = HERE / "runs" / "week-16"
sys.path.insert(0, str(COURSE))

from shared.governance import Denied, Platform, canonical  # noqa: E402
from shared.tracing import SimClock as TraceClock  # noqa: E402
from shared.tracing import Tracer, export_span, parse_traceparent, traceparent  # noqa: E402

QUEUE = json.loads((DATA / "queue-policy-v1.json").read_text())
DAY = json.loads((DATA / "day-script-v1.json").read_text())
DAY_START = datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc)
ACTIVE = ("queued", "leased")


def load_week_lab(folder: str, name: str):
    """Earlier weeks' labs run unchanged, loaded by path (Week 11's pattern)."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W12 = load_week_lab("week-12-release-gates", "week12_lab_for_w16")      # its W11 knows v2.1 to v2.4
W11 = W12.W11
W14 = load_week_lab("week-14-multi-tenant-governance", "week14_lab_for_w16")
RELEASE_POLICY = W12.load_policy()


# --- The queue's tables. They live in the platform's database, beside its usage table -----------

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY, seq INTEGER, tenant TEXT, actor TEXT, request_id TEXT, label TEXT,
    payload TEXT, cases INTEGER, reserve_usd REAL, traceparent TEXT, state TEXT,
    attempts INTEGER DEFAULT 0, lease_owner TEXT, lease_token INTEGER DEFAULT 0, lease_expires NUMERIC,
    not_before NUMERIC DEFAULT 0, enqueued_at NUMERIC, first_leased_at NUMERIC, last_lease_seq INTEGER,
    finished_at NUMERIC, result TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS job_events (seq INTEGER PRIMARY KEY AUTOINCREMENT, at NUMERIC, job_id TEXT,
    worker TEXT, kind TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS requests (request_id TEXT PRIMARY KEY, tenant TEXT, actor TEXT, spec TEXT,
    job_ids TEXT, submitted_at NUMERIC, finished_at NUMERIC, state TEXT, outcome TEXT);
CREATE TABLE IF NOT EXISTS usage (run_id TEXT, tenant TEXT, actor TEXT, cases INTEGER, cost_usd REAL);
CREATE UNIQUE INDEX IF NOT EXISTS usage_charged_once ON usage(run_id);
"""
JOB_COLUMNS = ("job_id", "seq", "tenant", "actor", "request_id", "label", "payload", "cases", "reserve_usd",
               "traceparent", "state", "attempts", "lease_owner", "lease_token", "lease_expires", "not_before",
               "enqueued_at", "first_leased_at", "last_lease_seq", "finished_at", "result", "error")


def open_queue(path: str) -> sqlite3.Connection:
    """A connection for one thread. The timeout makes a busy writer wait instead of failing."""
    conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL")       # readers do not block the one writer
        conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def write_lock(conn: sqlite3.Connection):
    """One transaction that takes SQLite's write lock at BEGIN, so no other worker changes what it reads."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


def job(conn: sqlite3.Connection, job_id: str) -> dict:
    row = conn.execute(f"SELECT {', '.join(JOB_COLUMNS)} FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    return dict(zip(JOB_COLUMNS, row))


def log_event(conn, at: float, job_id: str, worker: str | None, kind: str, detail: str = "") -> None:
    conn.execute("INSERT INTO job_events (at, job_id, worker, kind, detail) VALUES (?, ?, ?, ?, ?)",
                 (at, job_id, worker, kind, detail))


def enqueue(conn, spec: dict, now: float) -> bool:
    """Insert a job unless its ID exists. The ID is a hash of the work, so a resubmission is a no-op."""
    seq = conn.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM jobs").fetchone()[0]
    cur = conn.execute(
        "INSERT OR IGNORE INTO jobs (job_id, seq, tenant, actor, request_id, label, payload, cases, reserve_usd,"
        " traceparent, state, enqueued_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
        (spec["job_id"], seq, spec["tenant"], spec["actor"], spec["request_id"], spec["label"],
         json.dumps(spec["payload"]), spec["cases"], spec["reserve_usd"], spec.get("traceparent"), now))
    if cur.rowcount:
        log_event(conn, now, spec["job_id"], None, "enqueued", spec["label"])
    return cur.rowcount == 1


# --- Dispatch: which queued job a free worker gets ------------------------------------------------

def pick_job(conn, now: float, scheduler: str) -> str | None:
    """fifo: the oldest job. fair: the oldest job of the tenant served least recently (round robin)."""
    rows = conn.execute("SELECT job_id, tenant FROM jobs WHERE state='queued' AND not_before <= ? ORDER BY seq",
                        (now,)).fetchall()
    if not rows:
        return None
    if scheduler == "fifo":
        return rows[0][0]
    # ponytail: unweighted round robin by job, and a scan of every queued row per lease. Weight by expected
    # seconds when job sizes differ a lot; index (state, tenant, seq) when queues hold thousands of jobs.
    served = dict(conn.execute("SELECT tenant, MAX(COALESCE(last_lease_seq, 0)) FROM jobs GROUP BY tenant"))
    tenant = min({t for _j, t in rows}, key=lambda t: (served.get(t, 0), t))
    return next(j for j, t in rows if t == tenant)


def lease(conn, worker: str, now: float, scheduler: str = "fair", lease_seconds: float | None = None):
    """Give one queued job to `worker` until now + lease_seconds. Returns the job with its new token, or None."""
    lease_seconds = QUEUE["lease_seconds"] if lease_seconds is None else lease_seconds
    with write_lock(conn):                          # locked before choosing, so no two workers pick one job
        job_id = pick_job(conn, now, scheduler)
        if job_id is None:
            return None
        seq = conn.execute("SELECT COALESCE(MAX(last_lease_seq), 0) + 1 FROM jobs").fetchone()[0]
        conn.execute("UPDATE jobs SET state='leased', lease_owner=?, lease_token=lease_token+1, lease_expires=?,"
                     " attempts=attempts+1, first_leased_at=COALESCE(first_leased_at, ?), last_lease_seq=?"
                     " WHERE job_id=? AND state='queued'", (worker, now + lease_seconds, now, seq, job_id))
        leased = job(conn, job_id)
        log_event(conn, now, job_id, worker, "leased", f"attempt {leased['attempts']}, token {leased['lease_token']}")
        return leased


def complete(conn, leased: dict, result: dict, cost_usd: float, now: float) -> str:
    """Store the result and charge the tenant, once. A worker whose lease was taken over gets 'stale'."""
    with write_lock(conn):
        cur = conn.execute("UPDATE jobs SET state='done', result=?, finished_at=?, lease_owner=NULL"
                           " WHERE job_id=? AND state='leased' AND lease_token=?",
                           (json.dumps(result), now, leased["job_id"], leased["lease_token"]))
        outcome = "done" if cur.rowcount == 1 else "stale"
        if outcome == "done":                          # the charge commits with the result, or not at all
            conn.execute("INSERT INTO usage VALUES (?, ?, ?, ?, ?)",
                         (leased["job_id"], leased["tenant"], leased["actor"], leased["cases"], round(cost_usd, 6)))
        log_event(conn, now, leased["job_id"], leased["lease_owner"], outcome,
                  f"token {leased['lease_token']}, cost {cost_usd:.4f}")
    return outcome


def retry_or_dead(conn, leased: dict, error: str, now: float, backoff: float) -> str:
    """After a failed attempt: back to the queue after a back-off, or dead once attempts reach the limit."""
    if leased["attempts"] >= QUEUE["max_attempts"]:
        outcome, change, args = "dead", "state='dead', error=?, finished_at=?", (error, now)
    else:
        outcome, change, args = "retry", "state='queued', error=?, not_before=?", (error, now + backoff)
    cur = conn.execute(f"UPDATE jobs SET {change}, lease_owner=NULL WHERE job_id=? AND state='leased'"
                       " AND lease_token=?", (*args, leased["job_id"], leased["lease_token"]))
    if cur.rowcount == 0:
        return "stale"
    log_event(conn, now, leased["job_id"], leased["lease_owner"], outcome, error)
    return outcome


def fail(conn, leased: dict, error: str, now: float) -> str:
    """The worker reports an exception. Back-off doubles per attempt: 15 s, then 30 s."""
    with write_lock(conn):
        return retry_or_dead(conn, leased, error, now, QUEUE["backoff_seconds"] * 2 ** (leased["attempts"] - 1))


def expire_leases(conn, now: float) -> list[tuple[dict, str]]:
    """Requeue every job whose lease ran out: its worker died or stalled. No back-off, the job did not fail."""
    with write_lock(conn):
        ids = [r[0] for r in conn.execute("SELECT job_id FROM jobs WHERE state='leased' AND lease_expires <= ?"
                                          " ORDER BY seq", (now,))]
        out = []
        for job_id in ids:
            expired = job(conn, job_id)
            out.append((expired, retry_or_dead(conn, expired, f"lease expired ({expired['lease_owner']})", now, 0)))
        return out


# --- Admission: who may submit, and whether the platform takes the work now -----------------------

def build_platform(clock) -> Platform:
    """Week 14's platform with this week's budgets, and the queue's tables in the same database."""
    policy = json.loads(json.dumps(W14.TENANTS))
    for tenant, limits in QUEUE["tenants"].items():
        policy["tenants"][tenant].update(monthly_budget_usd=limits["budget_usd"],
                                         reserve_per_case_usd=limits["reserve_per_case_usd"])
    platform = Platform(policy, clock=clock, runners=W14.RUNNERS, names=W14.NAMES)
    platform.db.executescript(SCHEMA)
    return platform


def request_id(tenant: str, spec: dict) -> str:
    fields = {k: v for k, v in spec.items() if k not in ("at", "actor", "note")}
    return "req-" + hashlib.sha256(canonical({"tenant": tenant, **fields})).hexdigest()[:8]


def shards(records: list[dict], size: int) -> list[list[dict]]:
    return [records[i:i + size] for i in range(0, len(records), size)]


def plan_jobs(tenant: str, actor: str, rid: str, spec: dict, records: list[dict], dataset_sha: str) -> list[dict]:
    """Split a request into shard jobs. A job's ID hashes the work itself, not the request asking for it."""
    if spec["kind"] == "release":
        runs = [(version, name, cfg["config"]) for version in (spec["baseline"], spec["candidate"])
                for name, cfg in RELEASE_POLICY["runs"].items()]
        work = [{"runner": "suite", "suite": c["suite"], "agent": v, "backend": c["backend"], "judge": c["judge"],
                 "retries": c["retries"], "run": name} for v, name, c in runs]
    elif spec["kind"] == "suite":
        work = [{"runner": "suite", "suite": spec["suite"], "agent": spec["agent"], "backend": spec["backend"],
                 "judge": "none", "retries": 0, "run": spec["suite"]}]
    else:
        work = [{"runner": "retrieval", "retriever": spec["retriever"], "k": spec["k"], "run": "retrieval"}]
    reserve = QUEUE["tenants"][tenant]["reserve_per_case_usd"]
    jobs = []
    for w in work:
        parts = shards(records, QUEUE["shard_size"])
        for i, part in enumerate(parts):
            payload = {**w, "dataset_sha256": dataset_sha, "shard": i, "of": len(parts), "cases": part}
            job_id = "job-" + hashlib.sha256(canonical({"tenant": tenant, **payload})).hexdigest()[:10]
            label = f"{w.get('agent', w.get('retriever'))}/{w['run']}" + (f"@k{w['k']}" if "k" in w else "")
            jobs.append({"job_id": job_id, "tenant": tenant, "actor": actor, "request_id": rid,
                         "label": f"{label} shard {i + 1}/{len(parts)}", "payload": payload,
                         "cases": len(part), "reserve_usd": round(len(part) * reserve, 6)})
    return jobs


def active_jobs(conn, tenant: str | None = None) -> int:
    sql, args = "SELECT COUNT(*) FROM jobs WHERE state IN ('queued', 'leased')", ()
    if tenant:
        sql, args = sql + " AND tenant=?", (tenant,)
    return conn.execute(sql, args).fetchone()[0]


def reserved(conn, tenant: str) -> float:
    return conn.execute("SELECT COALESCE(SUM(reserve_usd), 0) FROM jobs WHERE tenant=? AND state IN"
                        " ('queued', 'leased')", (tenant,)).fetchone()[0]


def admit(platform: Platform, actor: str, spec: dict, now: float, tracer: Tracer | None = None,
          check_reserved: bool = True) -> dict:
    """Authorize, then check budget, the tenant's quota and the queue's capacity, then enqueue all or nothing."""
    conn, who = platform.db, platform.principal(actor)
    tenant = who.tenant if who else None
    rid = request_id(tenant or "?", spec)
    try:
        p = platform._authorize(actor, "eval.run", f"request:{rid}", tenant)    # Week 14's one access check
    except Denied as exc:
        return {"request_id": rid, "status": "denied", "reason": "role", "detail": str(exc)}
    if conn.execute("SELECT 1 FROM requests WHERE request_id=?", (rid,)).fetchone():
        return {"request_id": rid, "status": "duplicate", "reason": "", "detail": "same request already admitted"}
    dataset_ref = f"{tenant}/{spec['dataset']}"
    records = platform.read_dataset(actor, dataset_ref)                      # authorized, audited, hash-checked
    pinned = platform._resolve("dataset", dataset_ref, actor)[2]           # the version and hash read just now
    jobs = plan_jobs(tenant, actor, rid, spec, records, pinned["sha256"])
    existing = {r[0] for r in conn.execute(f"SELECT job_id FROM jobs WHERE job_id IN ({','.join('?' * len(jobs))})",
                                           [j["job_id"] for j in jobs])}
    new = [j for j in jobs if j["job_id"] not in existing]
    limits, need = QUEUE["tenants"][tenant], round(sum(j["reserve_usd"] for j in new), 6)
    held = reserved(conn, tenant) if check_reserved else 0.0
    spent = platform.spent(tenant)
    checks = [
        ("budget", spent + held + need > limits["budget_usd"] + 1e-9,
         f"spent {spent:.4f} + reserved {held:.4f} + this request {need:.4f} > {limits['budget_usd']}"),
        ("quota", active_jobs(conn, tenant) + len(new) > limits["max_active_jobs"],
         f"{active_jobs(conn, tenant)} active + {len(new)} new > {limits['max_active_jobs']} for {tenant}: retry later"),
        ("capacity", active_jobs(conn) + len(new) > QUEUE["capacity"],
         f"{active_jobs(conn)} active + {len(new)} new > queue capacity {QUEUE['capacity']}: retry later"),
    ]
    for reason, refused, detail in checks:
        if refused:
            platform._audit(actor, p, "eval.admit", f"request:{rid}", tenant, "deny", reason, detail)
            return {"request_id": rid, "status": "denied", "reason": reason, "detail": detail}
    root = None
    if tracer:
        with tracer.span("eval_request", "CHAIN", {"tenant": tenant, "request.id": rid,
                                                    "request.kind": spec["kind"]}) as root:
            pass                                       # stays open: end_ms is set when the request finishes
    for j in jobs:
        j["traceparent"] = traceparent(root) if root else None
    added = [j["job_id"] for j in jobs if enqueue(conn, j, now)]
    conn.execute("INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?, NULL, 'open', NULL)",
                 (rid, tenant, actor, json.dumps(spec), json.dumps([j["job_id"] for j in jobs]), now))
    conn.commit()
    platform._audit(actor, p, "eval.admit", f"request:{rid}", tenant, "allow", "",
                    f"{pinned['ref']} sha256 {pinned['sha256'][:12]}; {len(jobs)} jobs ({len(added)} new,"
                    f" {len(jobs) - len(added)} shared); reserved {need:.4f}")
    return {"request_id": rid, "status": "admitted", "reason": "", "jobs": len(jobs), "new": len(added),
            "reserved": need, "root": root}


# --- Running a job ---------------------------------------------------------------------------------

def execute(payload: dict, now_iso: str) -> tuple[dict, float]:
    """Run one shard with the earlier weeks' code. Returns (result, cost in SIMULATED dollars)."""
    if payload["runner"] == "retrieval":
        out = W14.run_retrieval(payload["cases"], payload["retriever"], payload["k"])
        return out, out["cost_usd"]
    art = W11.run_suite(payload["suite"], payload["agent"], payload["backend"] == "strict", judge=payload["judge"],
                        retries=payload["retries"], cases=payload["cases"], now=lambda: now_iso)
    return art, art["summary"]["cost_usd"]


def job_seconds(payload: dict) -> int:
    """SIMULATED duration: seconds per case for the job's runner."""
    key = "retrieval" if payload["runner"] == "retrieval" else f"suite:{payload['suite']}"
    return len(payload["cases"]) * QUEUE["seconds_per_case"][key]


# --- Finishing a request: merge shards, then decide ------------------------------------------------

def merge_shards(skeleton: dict, results: list[dict | None], expected: list[dict], workers: int,
                 dead: list[str]) -> dict:
    """One Week 11 artifact from shard artifacts. `skeleton` is the runner's run over zero cases: its run_id
    pins the code and data every shard must have used. Missing shards leave the run incomplete, never smaller."""
    done = [r for r in results if r]
    wrong = sorted({r["run_id"] for r in done} - {skeleton["run_id"]})
    if wrong:
        raise ValueError(f"shards ran other code or data: {wrong}, expected {skeleton['run_id']}")
    by_case = {c["case_id"]: c for r in done for c in r["cases"]}
    ordered = [by_case[c["case_id"]] for c in expected if c["case_id"] in by_case]
    return {**skeleton, "started_at": min([r["started_at"] for r in done], default=skeleton["started_at"]),
            "config": {**skeleton["config"], "workers": workers}, "expected_cases": len(expected),
            "completed_cases": len(ordered), "complete": len(ordered) == len(expected),
            "stop_reason": f"dead-lettered shards: {', '.join(dead)}" if dead else None,
            "summary": W11.summarize(ordered), "cases": ordered}


def finish_request(sim: dict, rid: str, now: float) -> dict:
    """Called once every job of the request is done or dead."""
    conn, platform = sim["conn"], sim["platform"]
    tenant, actor, spec, job_ids = conn.execute(
        "SELECT tenant, actor, spec, job_ids FROM requests WHERE request_id=?", (rid,)).fetchone()
    spec, jobs = json.loads(spec), [job(conn, j) for j in json.loads(job_ids)]
    out, p, workers = sim["out"] / rid, platform.principal(actor), len(QUEUE["workers"])
    groups = defaultdict(list)
    for j in jobs:
        pl = json.loads(j["payload"])
        groups[(pl.get("agent", pl.get("retriever")), pl["run"])].append((j, pl))
    folders = {}
    for (version, run), members in groups.items():
        if members[0][1]["runner"] == "retrieval":
            rows = [json.loads(j["result"])["metrics"] for j, _pl in members if j["result"]]
            n, total = sum(r["cases"] for r in rows), sum(len(pl["cases"]) for _j, pl in members)
            folders[run] = {"recall_at_5": round(sum(r["recall_at_5"] * r["cases"] for r in rows) / n, 4) if n else None,
                            "problems": [] if n == total else [f"incomplete run: {n} of {total} queries"]}
            continue
        expected = [c for _j, pl in sorted(members, key=lambda m: m[1]["shard"]) for c in pl["cases"]]
        skeleton = execute({**members[0][1], "cases": []}, iso(now))[0]
        art = merge_shards(skeleton, [json.loads(j["result"]) if j["result"] else None for j, _pl in members],
                           expected, workers, [j["job_id"] for j, _pl in members if j["state"] == "dead"])
        W11.write_artifact(art, out / version / run)
        folders[(version, run)] = out / version / run
    if spec["kind"] == "release":
        decision = W12.gate(out / spec["baseline"], out / spec["candidate"], RELEASE_POLICY, now=lambda: iso(now))
        W12.write_decision(decision, out / "decision")
        digest = hashlib.sha256((out / "decision" / "decision.json").read_bytes()).hexdigest()
        outcome = {"verdict": decision["verdict"], "exit_code": decision["exit_code"],
                   "reasons": W12.reasons(decision), "decision_sha256": digest}
        state, detail = "decided", f"{decision['verdict']}; decision sha256 {digest[:12]}"
        action = "release.decided"
    else:
        outcome = folders["retrieval"] if spec["kind"] == "retrieval" else \
            {"problems": W11.verify_artifact(next(iter(folders.values())))}
        state = "unfinished" if outcome["problems"] else "complete"
        detail = outcome["problems"][0] if outcome["problems"] else \
            (f"recall@5 {outcome['recall_at_5']}" if "recall_at_5" in outcome else "complete")
        action = f"eval.{state}"
    conn.execute("UPDATE requests SET finished_at=?, state=?, outcome=? WHERE request_id=?",
                 (now, state, json.dumps(outcome), rid))
    conn.commit()
    platform._audit(actor, p, action, f"request:{rid}", tenant, "allow", "", detail)
    root = sim["roots"].get(rid)
    if root:
        root.end_ms, root.status = int(now * 1000), "OK" if state in ("decided", "complete") else "ERROR"
        root.attributes["request.outcome"] = detail
    return {"request_id": rid, "state": state, **outcome}


# --- The simulated day ------------------------------------------------------------------------------

def iso(seconds: float) -> str:
    return (DAY_START + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


class DayClock:
    """SIMULATED wall clock for the platform's audit events: the simulation's current second."""

    def __init__(self):
        self.now = 0

    def __call__(self) -> str:
        return iso(self.now)


def trace_attempt(tracer: Tracer, leased: dict, start: float, end: float, status: str, note: str) -> None:
    """One EVALUATOR span per attempt, parented through the traceparent the job carried across the queue."""
    if not leased["traceparent"]:
        return
    trace_id, parent_id, _sampled = parse_traceparent(leased["traceparent"])
    tracer.clock.now_ms = int(start * 1000)
    with tracer.span("eval_job", "EVALUATOR", {"job.id": leased["job_id"], "job.label": leased["label"],
                                                "job.attempt": leased["attempts"], "worker": leased["lease_owner"],
                                                "tenant": leased["tenant"]}, parent=(trace_id, parent_id)) as span:
        tracer.clock.now_ms = int(end * 1000)
        span.status, span.status_message = ("OK", "") if status == "done" else ("ERROR", note)


def simulate(scheduler: str = "fair", out: Path = RUNS / "day", script: dict = DAY, faults: bool = True,
             check_reserved: bool = True, max_seconds: int = 3600) -> dict:
    """Replay the SIMULATED day: submissions, four workers, faults, merges and gate decisions."""
    clock = DayClock()
    platform = build_platform(clock)
    W14.seed(platform)
    tracer = Tracer(seed=16, clock=TraceClock())
    sim = {"conn": platform.db, "platform": platform, "out": out, "tracer": tracer, "roots": {},
           "admissions": [], "finished": {}, "stale": [], "wasted_usd": 0.0, "scheduler": scheduler}
    plan = script["faults"] if faults else {}
    workers = {w: {"alive": True, "leases": 0, "busy": None} for w in QUEUE["workers"]}
    pending = sorted(script["submissions"], key=lambda s: s["at"])
    for t in range(max_seconds):
        clock.now = t
        while pending and pending[0]["at"] <= t:
            spec = pending.pop(0)
            tracer.clock.now_ms = t * 1000
            res = admit(platform, spec["actor"], spec, t, tracer, check_reserved)
            if res.get("root"):
                sim["roots"][res["request_id"]] = res.pop("root")
            res.pop("root", None)
            sim["admissions"].append({"at": t, "actor": spec["actor"], "kind": spec["kind"],
                                      "what": spec.get("candidate") or spec.get("agent") or
                                      f"{spec.get('retriever')}@k{spec.get('k')}", **res})
        for name, w in workers.items():                       # workers whose current job ends now
            busy = w["busy"]
            if not busy or busy["until"] != t:
                continue
            w["busy"], leased = None, busy["job"]
            if busy["kind"] == "crash":
                w["alive"] = False
                continue
            if busy["kind"] == "poison":
                outcome = fail(platform.db, leased, "SIMULATED: the runner raised on this shard", t)
                trace_attempt(tracer, leased, busy["start"], t, outcome, "runner raised")
                continue
            outcome = complete(platform.db, leased, busy["result"], busy["cost"], t)
            trace_attempt(tracer, leased, busy["start"], t, outcome, "stale lease: result discarded")
            if outcome == "stale":
                sim["stale"].append({"job_id": leased["job_id"], "worker": name, "at": t})
                sim["wasted_usd"] += busy["cost"]
        for expired, outcome in expire_leases(platform.db, t):
            trace_attempt(tracer, expired, expired["lease_expires"] - QUEUE["lease_seconds"], t, outcome,
                          f"lease expired on {expired['lease_owner']}")
        for rid, in platform.db.execute("SELECT request_id FROM requests WHERE state='open'").fetchall():
            ids = json.loads(platform.db.execute("SELECT job_ids FROM requests WHERE request_id=?", (rid,)).fetchone()[0])
            states = {platform.db.execute("SELECT state FROM jobs WHERE job_id=?", (j,)).fetchone()[0] for j in ids}
            if not states & set(ACTIVE):
                sim["finished"][rid] = finish_request(sim, rid, t)
        for name, w in workers.items():                       # free workers take the next job
            if not w["alive"] or w["busy"]:
                continue
            leased = lease(platform.db, name, t, scheduler)
            if leased is None:
                continue
            w["leases"] += 1
            payload, seconds = json.loads(leased["payload"]), job_seconds(json.loads(leased["payload"]))
            poison = plan.get("poison", {})
            if poison and leased["tenant"] == poison["tenant"] and payload["shard"] == poison["shard"]:
                w["busy"] = {"job": leased, "until": t + 1, "kind": "poison", "start": t}
                continue
            result, cost = execute(payload, iso(t))
            busy = {"job": leased, "until": t + seconds, "kind": "done", "start": t, "result": result, "cost": cost}
            crash, pause = plan.get("crash", {}), plan.get("pause", {})
            if crash.get("worker") == name and crash["on_lease"] == w["leases"]:
                busy.update(kind="crash", until=t + seconds // 2)
                sim["wasted_usd"] += cost
            elif pause.get("worker") == name and pause["on_lease"] == w["leases"]:
                busy["until"] = t + seconds + pause["seconds"]
            w["busy"] = busy
        if not pending and not active_jobs(platform.db) and not any(w["busy"] for w in workers.values()):
            break
    sim.update(end=t, workers={n: {"alive": w["alive"], "leases": w["leases"]} for n, w in workers.items()})
    return sim


# --- Measuring the day ------------------------------------------------------------------------------

def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile: the smallest value with at least pct of the values at or below it."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct * len(ordered)) - 1)] if ordered else float("nan")


def tenant_stats(sim: dict) -> dict:
    """Queue wait (enqueue to first lease) per tenant, in SIMULATED seconds."""
    rows = sim["conn"].execute("SELECT tenant, first_leased_at - enqueued_at FROM jobs WHERE first_leased_at"
                               " IS NOT NULL").fetchall()
    waits = defaultdict(list)
    for tenant, wait in rows:
        waits[tenant].append(wait)
    return {t: {"jobs": len(w), "p50": percentile(w, 0.5), "p95": percentile(w, 0.95), "max": max(w)}
            for t, w in sorted(waits.items())}


def request_rows(sim: dict) -> list[dict]:
    rows = sim["conn"].execute("SELECT request_id, tenant, spec, submitted_at, finished_at, state, outcome"
                               " FROM requests ORDER BY rowid").fetchall()
    return [{"request_id": r, "tenant": t, "spec": json.loads(s), "submitted": a, "finished": f,
             "latency": None if f is None else f - a, "state": st, "outcome": json.loads(o) if o else None}
            for r, t, s, a, f, st, o in rows]


def slo_report(sim: dict) -> list[dict]:
    """The two SLOs in the queue policy, measured on the SIMULATED day."""
    slo, out = QUEUE["slo"], []
    for r in request_rows(sim):
        if r["spec"]["kind"] == "release":
            out.append({"slo": f"release decision within {slo['release_decision_seconds']} s", "subject": r["request_id"],
                        "measured": r["latency"], "met": r["latency"] is not None
                        and r["latency"] <= slo["release_decision_seconds"]})
    for tenant, s in tenant_stats(sim).items():
        out.append({"slo": f"queue wait p95 within {slo['queue_wait_p95_seconds']} s", "subject": tenant,
                    "measured": s["p95"], "met": s["p95"] <= slo["queue_wait_p95_seconds"]})
    return out


def job_history(sim: dict, job_id: str) -> list[tuple]:
    return sim["conn"].execute("SELECT at, worker, kind, detail FROM job_events WHERE job_id=? ORDER BY seq",
                               (job_id,)).fetchall()


def fault_jobs(sim: dict) -> dict:
    """The jobs the fault plan hit: leased more than once, or dead."""
    ids = [r[0] for r in sim["conn"].execute("SELECT job_id FROM jobs WHERE attempts > 1 OR state='dead' ORDER BY seq")]
    return {j: job_history(sim, j) for j in ids}


def charges(sim: dict) -> dict:
    """Usage rows per job: exactly one for every finished job, none for a dead one."""
    rows = sim["conn"].execute("SELECT j.state, COUNT(u.run_id) FROM jobs j LEFT JOIN usage u ON u.run_id = j.job_id"
                               " GROUP BY j.job_id").fetchall()
    return dict(Counter((state, n) for state, n in rows))


def request_audit(sim: dict, rid: str) -> list[dict]:
    """The audit trail for one request, as the platform auditor sees it."""
    return [e for e in sim["platform"].audit("platform.auditor") if e["resource"] == f"request:{rid}"]


# --- Drills --------------------------------------------------------------------------------------------

def run_job_through_platform(platform: Platform, leased: dict) -> dict:
    """Drill 1, BROKEN: the worker calls Week 14's run_eval, which charges inside the job, before the ack."""
    payload = json.loads(leased["payload"])
    return platform.run_eval(leased["actor"], f"{leased['tenant']}/tool-cases", [], agent=payload["agent"],
                             strict=payload["backend"] == "strict")


def double_charge_drill(fixed: bool) -> list[tuple]:
    """A worker runs a job, then dies before reporting. The lease expires and a second worker reruns it.
    Returns the usage rows: what the tenant was charged."""
    clock = DayClock()
    platform = build_platform(clock)
    refs = W14.seed(platform)
    conn = platform.db
    records = platform.read_dataset("refunds.engineer", refs["tool-cases"])
    enqueue(conn, {"job_id": "job-drill-1", "tenant": "refunds-agent", "actor": "refunds.engineer",
                   "request_id": "drill-1", "label": "v2/release all 30 cases", "cases": len(records),
                   "reserve_usd": 0.045, "payload": {"runner": "suite", "suite": "tools", "agent": "v2",
                   "backend": "strict", "judge": "none", "retries": 0, "run": "release", "shard": 0, "of": 1,
                   "cases": records}}, 0)
    conn.commit()
    for t, worker in ((0, "w1"), (60, "w2")):
        clock.now = t
        expire_leases(conn, t)                     # at t=60, w1's lease has run out
        leased = lease(conn, worker, t)
        if not fixed:
            run_job_through_platform(platform, leased)
        else:
            result, cost = execute(json.loads(leased["payload"]), iso(t))
            if worker == "w2":                     # w1 died before this line
                complete(conn, leased, result, cost, t)
    return conn.execute("SELECT run_id, tenant, cases, cost_usd FROM usage ORDER BY rowid").fetchall()


def merge_present_shards(skeleton: dict, results: list[dict | None], expected: list[dict], workers: int,
                         dead: list[str]) -> dict:
    """Drill 2, BROKEN: expects only the cases that came back, so a dead shard disappears from the run."""
    present = {c["case_id"] for r in results if r for c in r["cases"]}
    return merge_shards(skeleton, results, [c for c in expected if c["case_id"] in present], workers, [])


# --- Real threads: the same queue functions under concurrency -----------------------------------------

def thread_trial(path: Path, n_jobs: int, n_threads: int, io_seconds: float = 0.0, crash_job: int = 3,
                 lease_seconds: float = 1.0) -> dict:
    """n_threads workers drain n_jobs from a SQLite file. The worker that leases job `crash_job` first dies
    holding the lease and restarts under a new name. A job does no work beyond the queue's own reads and
    writes, unless io_seconds adds a sleep as a SIMULATED stand-in for waiting on a model API."""
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)
    setup = open_queue(str(path))
    for i in range(n_jobs):
        enqueue(setup, {"job_id": f"t-{i:04d}", "tenant": ("support-rag", "refunds-agent", "trust-safety")[i % 3],
                        "actor": "load.test", "request_id": "threads", "label": f"job {i}", "payload": {"i": i},
                        "cases": 1, "reserve_usd": 0.001}, time.monotonic())
    setup.commit()
    setup.close()
    crashed, lock = [], threading.Lock()

    def worker(name: str) -> None:
        conn, incarnation = open_queue(str(path)), 0
        while True:
            now = time.monotonic()
            leased = lease(conn, f"{name}.{incarnation}", now, "fair", lease_seconds)
            if leased is None:
                if not active_jobs(conn):
                    break
                expire_leases(conn, now)               # someone may have died holding the last jobs
                time.sleep(0.01)
                continue
            with lock:
                crash = leased["job_id"] == f"t-{crash_job:04d}" and not crashed
                if crash:
                    crashed.append(leased["lease_owner"])
            if crash:                                  # the process dies holding the lease, then restarts
                conn.close()
                conn, incarnation = open_queue(str(path)), incarnation + 1
                continue
            if io_seconds:
                time.sleep(io_seconds)
            complete(conn, leased, {"ok": True}, 0.001, time.monotonic())
        conn.close()

    start = time.monotonic()
    threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(n_threads)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    wall = time.monotonic() - start
    conn = open_queue(str(path))
    done = conn.execute("SELECT COUNT(*) FROM jobs WHERE state='done'").fetchone()[0]
    charged = conn.execute("SELECT COUNT(*), COUNT(DISTINCT run_id) FROM usage").fetchone()
    in_system = [r[0] for r in conn.execute("SELECT finished_at - enqueued_at FROM jobs WHERE state='done'")]
    retried = conn.execute("SELECT COUNT(*) FROM jobs WHERE attempts > 1").fetchone()[0]
    stale = conn.execute("SELECT COUNT(*) FROM job_events WHERE kind='stale'").fetchone()[0]
    conn.close()
    return {"threads": n_threads, "jobs": n_jobs, "done": done, "usage_rows": charged[0], "charged_jobs": charged[1],
            "retried": retried, "stale": stale, "crashed_worker": crashed[0] if crashed else None,
            "wall_s": wall, "jobs_per_s": n_jobs / wall,
            "p50_ms": percentile(in_system, 0.5) * 1000, "p95_ms": percentile(in_system, 0.95) * 1000}


# --- Printing and the dashboard ---------------------------------------------------------------------

def print_admissions(sim: dict) -> None:
    print(f"{'t':>4}  {'actor':17} {'request':13} {'kind':9} {'what':13} {'status':10} detail")
    for a in sim["admissions"]:
        detail = a["detail"] if a["status"] != "admitted" else f"{a['jobs']} jobs, {a['new']} new, reserved {a['reserved']:.4f}"
        print(f"{a['at']:>4}  {a['actor']:17} {a['request_id']:13} {a['kind']:9} {a['what']:13} "
              f"{a['status'] + (':' + a['reason'] if a['reason'] else ''):10} {detail}")


def outcome_text(r: dict) -> str:
    o = r["outcome"] or {}
    if "verdict" in o:
        return f"{o['verdict']}: {(o['reasons'] or ['every rule passed'])[0][:72]}"
    if o.get("problems"):
        return f"UNFINISHED: {o['problems'][0][:72]}"
    return f"recall@5 {o['recall_at_5']}" if "recall_at_5" in o else r["state"]


def print_requests(sim: dict) -> None:
    print(f"{'request':13} {'tenant':14} {'kind':9} {'what':13} {'submitted':>9} {'finished':>8} {'latency':>7}  outcome")
    for r in request_rows(sim):
        s = r["spec"]
        what = s.get("candidate") or s.get("agent") or f"{s.get('retriever')}@k{s.get('k')}"
        outcome = outcome_text(r)
        print(f"{r['request_id']:13} {r['tenant']:14} {s['kind']:9} {what:13} {r['submitted']:>9} "
              f"{'-' if r['finished'] is None else r['finished']:>8} {'-' if r['latency'] is None else r['latency']:>7}  {outcome}")


def print_waits(sim: dict) -> None:
    print(f"{'tenant':14} {'jobs':>5} {'wait p50':>9} {'p95':>6} {'max':>6}   (SIMULATED seconds)")
    for t, s in tenant_stats(sim).items():
        print(f"{t:14} {s['jobs']:>5} {s['p50']:>9} {s['p95']:>6} {s['max']:>6}")


def print_demo(sim: dict) -> None:
    print(f"SIMULATED day, scheduler={sim['scheduler']}, {len(QUEUE['workers'])} workers, "
          f"lease {QUEUE['lease_seconds']} s, max {QUEUE['max_attempts']} attempts. Ended at t={sim['end']} s.\n")
    print("Admission")
    print_admissions(sim)
    print("\nRequests")
    print_requests(sim)
    print("\nQueue wait")
    print_waits(sim)
    usage = {u["tenant"]: u for u in sim["platform"].usage("platform.auditor")}
    print("\nCharges (Week 14 usage table, SIMULATED dollars)")
    for t, u in usage.items():
        print(f"  {t:14} {u['runs']:>3} jobs  {u['cases']:>4} cases  ${u['cost_usd']:.4f} of ${u['budget_usd']:.2f}")
    c = charges(sim)
    print(f"  usage rows per job: {', '.join(f'{s} x{n}: {k}' for (s, n), k in sorted(c.items()))}")
    print(f"  stale completions rejected: {len(sim['stale'])}, SIMULATED work wasted: ${sim['wasted_usd']:.4f}")
    print("\nSLOs (SIMULATED day)")
    for s in slo_report(sim):
        print(f"  {'met   ' if s['met'] else 'BREACH'} {s['slo']:34} {s['subject']:14} measured {s['measured']}")
    print(f"\nAudit chain: {len(sim['platform'].audit('platform.auditor'))} events, "
          f"problems: {sim['platform'].verify_audit() or 'none'}")


def print_compare(fifo: dict, fair: dict) -> None:
    print("Same SIMULATED day, same faults, two dispatch rules.\n")
    print(f"{'tenant':14} {'fifo p50':>9} {'p95':>5} {'max':>5}   {'fair p50':>9} {'p95':>5} {'max':>5}")
    a, b = tenant_stats(fifo), tenant_stats(fair)
    for t in a:
        print(f"{t:14} {a[t]['p50']:>9} {a[t]['p95']:>5} {a[t]['max']:>5}   {b[t]['p50']:>9} {b[t]['p95']:>5} {b[t]['max']:>5}")
    print(f"\n{'release request':16} {'candidate':10} {'fifo latency':>12} {'fair latency':>12}  verdict")
    fr = {r["request_id"]: r for r in request_rows(fair)}
    for r in request_rows(fifo):
        if r["spec"]["kind"] == "release" and r["latency"] is not None:
            v = r["outcome"]["verdict"]
            print(f"{r['request_id']:16} {r['spec']['candidate']:10} {r['latency']:>12} {fr[r['request_id']]['latency']:>12}  {v}")
    for name, sim in (("fifo", fifo), ("fair", fair)):
        breaches = [f"{s['subject']} ({s['measured']})" for s in slo_report(sim) if not s["met"]]
        print(f"SLO breaches, {name}: {', '.join(breaches) or 'none'}")


def print_faults(sim: dict) -> None:
    print("Jobs hit by the SIMULATED fault plan (job_events):")
    for job_id, events in fault_jobs(sim).items():
        j = job(sim["conn"], job_id)
        print(f"\n{job_id} {j['tenant']} {j['label']}: final state {j['state']}, {j['attempts']} attempts")
        for at, worker, kind, detail in events:
            print(f"  t={at:>4}  {worker or '-':4} {kind:8} {detail}")
    alive = [f"{n} {'alive' if w['alive'] else 'DEAD'} ({w['leases']} leases)" for n, w in sim["workers"].items()]
    print(f"\nWorkers: {', '.join(alive)}")
    print(f"Usage rows per job: {dict(sorted(charges(sim).items()))}")


def print_audit(sim: dict, rid: str) -> None:
    events = request_audit(sim, rid)
    print(f"Audit trail for {rid} (Week 14 hash-chained log, SIMULATED clock):")
    for e in events:
        print(f"  {e['seq']:>4} {e['at']} {e['actor']:17} {e['action']:16} {e['decision']:5} "
              f"{(e['reason'] + ': ') if e['reason'] else ''}{e['detail']}")
    anchor = sim["platform"].audit_head()
    print(f"Chain: {sim['platform'].verify_audit(anchor) or 'intact'}; anchor seq {anchor[0]} {anchor[1][:12]}")


def write_dashboard(sim: dict, out: Path = RUNS / "dashboard") -> Path:
    """A static HTML page: SLOs, tenants, requests with links to decisions and traces, faults, the audit head."""
    (out / "traces").mkdir(parents=True, exist_ok=True)
    spans = sim["tracer"].spans
    for rid, root in sim["roots"].items():
        trace = [export_span(s, W14.NAMES, "week-16") for s in spans if s.trace_id == root.trace_id]
        (out / "traces" / f"{rid}.json").write_text(json.dumps(trace, indent=2))
    esc = html.escape
    slo = "".join(f"<tr class={'ok' if s['met'] else 'hot'}><td>{esc(s['slo'])}</td><td>{esc(s['subject'])}</td>"
                  f"<td>{s['measured']}</td><td>{'met' if s['met'] else 'BREACH'}</td></tr>" for s in slo_report(sim))
    usage = {u["tenant"]: u for u in sim["platform"].usage("platform.auditor")}
    tenants = "".join(f"<tr><td>{t}</td><td>{s['jobs']}</td><td>{s['p50']}</td><td>{s['p95']}</td><td>{s['max']}</td>"
                      f"<td>${usage[t]['cost_usd']:.4f}</td><td>${usage[t]['budget_usd']:.2f}</td></tr>"
                      for t, s in tenant_stats(sim).items())
    reqs = []
    for r in request_rows(sim):
        o, rid = r["outcome"] or {}, r["request_id"]
        result = o.get("verdict") or (o.get("problems") and "UNFINISHED") or r["state"]
        link = f" <a href='../day/{rid}/decision/decision.md'>decision</a>" if o.get("verdict") else ""
        trace = f"<a href='traces/{rid}.json'>trace</a>" if rid in sim["roots"] else ""
        reqs.append(f"<tr class={'hot' if result in ('BLOCK', 'UNFINISHED') else ''}><td>{rid}</td><td>{r['tenant']}</td>"
                    f"<td>{esc(json.dumps({k: v for k, v in r['spec'].items() if k not in ('at', 'actor', 'note')}))}</td>"
                    f"<td>{r['latency']}</td><td>{esc(str(result))}{link}</td><td>{trace}</td></tr>")
    denied = "".join(f"<li>t={a['at']} {esc(a['actor'])} {a['request_id']}: {a['reason']}, {esc(a['detail'])}</li>"
                     for a in sim["admissions"] if a["status"] == "denied")
    faults = "".join(f"<li>{j}: " + "; ".join(f"t={at} {w or '-'} {k}" for at, w, k, _d in ev) + "</li>"
                     for j, ev in fault_jobs(sim).items())
    seq, head = sim["platform"].audit_head()
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Week 16 evaluation platform dashboard (SIMULATED)</title>
<style>body{{font:14px system-ui,sans-serif;margin:2rem;color:#222}}table{{border-collapse:collapse;margin-bottom:1rem}}
td,th{{border:1px solid #ccc;padding:2px 6px;text-align:left}}tr.hot{{background:#fff0f0}}tr.ok{{background:#f2fbf2}}</style>
</head><body><h1>Shared evaluation platform: one SIMULATED day</h1>
<p>Generated by weeks/week-16-distributed-evaluation-capstone/handson/lab.py. Scheduler {sim['scheduler']},
{len(QUEUE['workers'])} workers. Every time is SIMULATED seconds, every dollar SIMULATED. Prototype numbers, not capacity.</p>
<h2>SLOs</h2><table><tr><th>objective</th><th>subject</th><th>measured</th><th>status</th></tr>{slo}</table>
<h2>Tenants</h2><table><tr><th>tenant</th><th>jobs</th><th>wait p50</th><th>p95</th><th>max</th><th>charged</th>
<th>budget</th></tr>{tenants}</table>
<h2>Requests</h2><table><tr><th>request</th><th>tenant</th><th>spec</th><th>latency s</th><th>result</th><th>trace</th>
</tr>{''.join(reqs)}</table><h2>Admission denials</h2><ul>{denied}</ul><h2>Faults and recovery</h2><ul>{faults}</ul>
<h2>Audit</h2><p>{seq} events, chain {'intact' if not sim['platform'].verify_audit() else 'BROKEN'}, head {head[:16]}.
Store the head outside this machine.</p></body></html>"""
    (out / "dashboard.html").write_text(page)
    return out / "dashboard.html"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "compare", "faults", "audit", "dashboard"):
        sub.add_parser(name)
    th = sub.add_parser("threads", help="real threads on a SQLite file; wall-clock numbers from this machine")
    th.add_argument("--jobs", type=int, default=2000)
    th.add_argument("--io-ms", type=float, default=0.0, help="SIMULATED wait per job; check the timer first")
    args = parser.parse_args(argv)
    if args.command == "threads":
        t0 = time.perf_counter()
        time.sleep(0.005)
        print(f"Timer check: time.sleep(0.005) took {(time.perf_counter() - t0) * 1000:.0f} ms on this machine.")
        print(f"Real threads, SQLite file (WAL), {args.jobs} jobs, {args.io_ms:g} ms SIMULATED I/O per job,"
              " one worker killed holding a lease.")
        print("Wall-clock numbers measured on this machine: prototype measurements, not production capacity.")
        print(f"{'threads':>7} {'done':>5} {'charged':>8} {'retried':>8} {'stale':>6} {'jobs/s':>7} {'p50 ms':>7} {'p95 ms':>7}")
        RUNS.mkdir(parents=True, exist_ok=True)
        for n in (1, 2, 4, 8):
            r = thread_trial(RUNS / "threads.db", args.jobs, n, args.io_ms / 1000)
            print(f"{n:>7} {r['done']:>5} {r['charged_jobs']:>8} {r['retried']:>8} {r['stale']:>6} "
                  f"{r['jobs_per_s']:>7.0f} {r['p50_ms']:>7.0f} {r['p95_ms']:>7.0f}")
        return 0
    if args.command == "compare":
        print_compare(simulate("fifo", RUNS / "fifo"), simulate("fair", RUNS / "day"))
        return 0
    sim = simulate("fair", RUNS / "day")
    if args.command == "demo":
        print_demo(sim)
    elif args.command == "faults":
        print_faults(sim)
    elif args.command == "audit":
        rid = next(r["request_id"] for r in request_rows(sim) if r["outcome"] and r["outcome"].get("verdict") == "BLOCK")
        print_audit(sim, rid)
    else:
        path = write_dashboard(sim)
        print(f"wrote {path.relative_to(COURSE)} and {len(list((path.parent / 'traces').glob('*.json')))} traces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
