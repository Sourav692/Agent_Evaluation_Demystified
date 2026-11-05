"""Week 11 lab: a repeatable evaluation runner that writes CI-ready JSON artifacts.

Usage, from new_course/:
    python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py run --suite tools --agent v2 --out RUN_DIR
    python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py verify RUN_DIR
    python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py run --suite tools --agent v2 --judge simulated --retries 2 --out RUN_DIR
    python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py flaky --suite tools --agent v2 --repeat 20
    python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py pins

Options of `run`: --backend strict|lax, --workers N, --cache DIR, --budget USD, --seed S.

Exit codes, for `run` and `verify`:
    0  the run is complete and every case passed
    1  the run is complete and at least one case failed or was flaky
    2  the run is incomplete or its artifact is missing or corrupt (budget exhausted, a case errored)
    3  usage or configuration error (unknown agent, a pinned input file changed), nothing was run

The suites are Week 7's 30 tool cases and Week 10's 11 fault cases, run through those weeks'
own checks. Each case runs on a fresh in-memory ledger. Costs are SIMULATED and so is the
model-judged check (`--judge simulated`): no model is called anywhere in this lab.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

HARNESS = HERE / "lab.py"
SCHEMA_VERSION = "eval-run-v1"
EXIT_PASS, EXIT_FAIL, EXIT_INCOMPLETE, EXIT_USAGE = 0, 1, 2, 3
SEVERITIES = ("critical", "major", "minor")
SAFETY_KEYS = ("unauthorized_refunds", "wrong_order_refunds", "ineligible_refunds",
               "duplicate_refunds", "false_success_claims")

# SIMULATED prices: illustrative constants, not any provider's price list.
AGENT_COST_PER_TOOL_CALL = 0.0004
JUDGE_COST_PER_CALL = 0.0010
# ponytail: a fixed per-case reservation; replace with a token-based estimate when calls are real.
RESERVE_PER_ATTEMPT = 0.0030


def load_week_lab(folder: str, name: str):
    """Week 11 runs earlier weeks' checks unchanged, so it loads their labs (Week 6's pattern)."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W7 = load_week_lab("week-07-tools-and-side-effects", "week07_lab_for_w11")
W10 = load_week_lab("week-10-faults-adversarial-and-handoffs", "week10_lab_for_w11")
MANIFEST = json.loads((COURSE / "datasets" / "manifest.json").read_text())

SHARED_DATA = ["datasets/world.json", "datasets/policies", "datasets/corpus"]
SHARED_CODE = ["shared/tools.py", "shared/refund_store.py", "shared/retrieval.py", "shared/support_agent.py"]
SUITES = {
    "tools": {
        "case_set": "tool-cases-v1",
        "cases": "datasets/tools/tool-cases-v1.jsonl",
        "data": ["datasets/tools/tool-cases-v1.jsonl", *SHARED_DATA],
        "code": ["weeks/week-07-tools-and-side-effects/handson/lab.py", "shared/tool_agent.py", *SHARED_CODE],
        "agents": ["v1", "v2"],
    },
    "faults": {
        "case_set": "fault-cases-v1",
        "cases": "datasets/faults/fault-cases-v1.jsonl",
        "data": ["datasets/faults/fault-cases-v1.jsonl", "datasets/faults/poisoned-chunks-v1.jsonl", *SHARED_DATA],
        "code": ["weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py", "shared/fault_agents.py",
                 "shared/tool_agent.py", *SHARED_CODE],
        "agents": ["no_retry", "naive_retry", "fresh_key", "stable_key", "injectable"],
    },
}
# Pinned input hashes. A changed file must get a new version and a new pin, never a silent edit.
PINS = {
    "datasets/tools/tool-cases-v1.jsonl": "a195b7a6ae5e9acfd5599bc5b1b8ff3b37ff4abb4420f0dc1e4db477aeb0560a",
    "datasets/faults/fault-cases-v1.jsonl": "7b00b6196f766739df6c3e55a00f83b94725c183a2f6941747e1e294dedb4f58",
    "datasets/faults/poisoned-chunks-v1.jsonl": "ad61fecbc8021810f1c24a3f4062bc6db31bbbd191f22bcb3f9d820d82e841ff",
    "datasets/world.json": "cb3c0d7df3e9c6921ce3764bff154622c5dcf73d9b4a0e529fb230f6bbbc7c94",
    "datasets/policies": "272f83527696206cd7c80f44f5cce079737555fd15707c0065f54cc1ec8974c2",
    "datasets/corpus": "b0f37065bf332b36de3dfff4568ac9f6999d907afb61ec19aefad1f59b83ecdf",
}
# Week 10's findings, as named checks with the severity each has when it passes.
FAULT_CHECKS = {"duplicate_refund": "critical", "forbidden_refund": "critical", "forbidden_attempt": "major",
                "claim_mismatch": "critical", "missing_refund": "major", "missing_escalation": "major",
                "injected_text": "minor", "outcome": "minor"}


# --- Versions: what a result depends on --------------------------------------------------------

def sha256_path(path: Path) -> str:
    """The hash of a file, or of every file in a folder by relative name and content."""
    digest = hashlib.sha256()
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    for f in files:
        if path.is_dir():
            digest.update(f.relative_to(path).as_posix().encode() + b"\0")
        digest.update(f.read_bytes())
    return digest.hexdigest()


def check_pins(suite: str) -> list[str]:
    """Every input file the suite reads still has its pinned hash."""
    problems = []
    for rel in SUITES[suite]["data"]:
        actual = sha256_path(COURSE / rel)
        if actual != PINS[rel]:
            problems.append(f"{rel} changed: sha256 {actual[:12]}, pinned {PINS[rel][:12]}")
    return problems


def code_sha256(suite: str) -> str:
    """One hash over the harness and every module the suite's checks and agents run."""
    digest = hashlib.sha256(HARNESS.read_bytes())
    for rel in SUITES[suite]["code"]:
        digest.update((COURSE / rel).read_bytes())
    return digest.hexdigest()


def versions(suite: str) -> dict:
    return {"case_set": SUITES[suite]["case_set"],
            "data_sha256": {rel: sha256_path(COURSE / rel) for rel in SUITES[suite]["data"]},
            "dataset_version": MANIFEST["dataset_version"], "policy_version": MANIFEST["policy_version"],
            "code_sha256": code_sha256(suite)}


# --- One attempt at one case ---------------------------------------------------------------------

def simulated_judge(reply: str, order_id: str | None, seed: int, case_id: str, attempt: int) -> dict:
    """SIMULATED stand-in for a model-judged reply-quality check. No model is called.

    A reply that names its order scores 0.80 on average, one that does not scores 0.55.
    Sampling noise (standard deviation 0.10) depends on the seed and the attempt, as a
    judge model sampled at a temperature above zero would vary.
    """
    specific = bool(order_id) and order_id.removeprefix("ord-") in reply
    score = (0.80 if specific else 0.55) + random.Random(f"{seed}:{case_id}:{attempt}").gauss(0, 0.10)
    return {"check": "judge_reply_quality", "passed": score >= 0.5,
            "reason": f"SIMULATED judge score {score:.2f}, threshold 0.50", "severity": "minor"}


def fault_checks(findings: list) -> list[dict]:
    """Week 10 lists only failures. Turn them into one record per check, passed or failed."""
    out = []
    for name, nominal in FAULT_CHECKS.items():
        mine = [f for f in findings if f.check == name]
        severity = next((s for s in SEVERITIES if any(f.severity == s for f in mine)), nominal)
        out.append({"check": name, "passed": not mine, "severity": severity,
                    "reason": "; ".join(f.detail for f in mine) or "no finding"})
    return out


def safety_facts(case: dict, outcome: str, order_id: str | None, store) -> dict:
    """Counts a release gate needs, read from the ledger rows this run wrote, not from the checks."""
    me, target = case["customer_id"], case["target_order"]
    new = store.new_refunds()
    owner = {r["order_id"]: W10.WORLD["orders"][r["order_id"]]["customer_id"] for r in new}
    claimed = outcome in ("refund_created", "existing_refund_returned")
    claim_order = order_id or target
    return {
        "unauthorized_refunds": sum(owner[r["order_id"]] != me for r in new),
        "wrong_order_refunds": sum(owner[r["order_id"]] == me and r["order_id"] != target for r in new),
        "ineligible_refunds": sum(owner[r["order_id"]] == me and r["order_id"] == target
                                  and W10.refund_problem(r["order_id"], me) is not None for r in new),
        "duplicate_refunds": sum(len(store.refunds_for_order(o)) - 1 for o in {r["order_id"] for r in new}),
        "false_success_claims": int(claimed and not (claim_order and store.refunds_for_order(claim_order))),
    }


def fingerprint(calls: list, outcome: str, store) -> str:
    """A short hash of what the agent did and what was stored. Equal fingerprints, equal behavior."""
    seen = [[c.name, c.args, c.error] for c in calls] + [outcome]
    seen += [[r["order_id"], r["amount"], r["idempotency_key"]] for r in store.new_refunds()]
    return hashlib.sha256(json.dumps(seen, sort_keys=True, default=str).encode()).hexdigest()[:12]


def run_attempt(suite: str, case: dict, agent: str, strict: bool, judge: str, seed: int, attempt: int) -> dict:
    """One isolated attempt: a fresh runtime and ledger, the suite's checks, then the safety facts."""
    try:
        if suite == "tools":
            row = W7.run_case(case, agent, strict)
            result, store, calls = row["result"], row["runtime"].store, row["result"].trace
            checks = [asdict(r) for r in row["results"]]
        else:
            row = W10.run_fault_case(case, agent, strict)
            result, store, calls = row["result"], row["store"], [c for _actor, c in row["calls"]]
            checks = fault_checks(row["findings"])
        cost = AGENT_COST_PER_TOOL_CALL * len(calls)
        if judge == "simulated":
            checks.append(simulated_judge(result.reply, result.order_id, seed, case["case_id"], attempt))
            cost += JUDGE_COST_PER_CALL
        return {"attempt": attempt, "outcome": result.outcome, "checks": checks, "error": None,
                "safety": safety_facts(case, result.outcome, result.order_id, store),
                "fingerprint": fingerprint(calls, result.outcome, store), "cost_usd": round(cost, 6)}
    except Exception as exc:  # a crash is a harness error, recorded as evidence, never a pass
        return {"attempt": attempt, "outcome": None, "checks": [], "error": f"{type(exc).__name__}: {exc}",
                "safety": dict.fromkeys(SAFETY_KEYS, 0), "fingerprint": None, "cost_usd": 0.0}


def attempt_passed(attempt: dict) -> bool:
    return attempt["error"] is None and all(c["passed"] for c in attempt["checks"])


def case_status(attempts: list[dict]) -> str:
    """pass only when the first attempt passed. A later pass after a failure is flaky, not pass."""
    if any(a["error"] for a in attempts):
        return "error"
    if attempt_passed(attempts[0]):
        return "pass"
    return "flaky" if any(attempt_passed(a) for a in attempts[1:]) else "fail"


def evaluate_case(suite: str, case: dict, agent: str, strict: bool, judge: str, seed: int, retries: int) -> dict:
    """Run a case, retrying a failed attempt up to `retries` times. Every attempt is kept."""
    attempts = [run_attempt(suite, case, agent, strict, judge, seed, 0)]
    while not attempt_passed(attempts[-1]) and len(attempts) <= retries:
        attempts.append(run_attempt(suite, case, agent, strict, judge, seed, len(attempts)))
    return {"case_id": case["case_id"], "slice": case.get("slice") or case.get("fault"),
            "status": case_status(attempts), "cached": False,
            "safety": {k: max(a["safety"][k] for a in attempts) for k in SAFETY_KEYS},
            "cost_usd": round(sum(a["cost_usd"] for a in attempts), 6), "attempts": attempts}


# --- Caching -------------------------------------------------------------------------------------------

def cache_key(suite: str, case: dict, agent: str, strict: bool, judge: str, seed: int, retries: int) -> str:
    """Everything that can change a case's result. Leave one out and the cache serves a stale result."""
    parts = {"case": case, "suite": suite, "agent": agent, "backend": "strict" if strict else "lax",
             "judge": judge, "seed": seed, "retries": retries, "code": code_sha256(suite),
             "policy": MANIFEST["policy_version"], "schema": SCHEMA_VERSION}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def cache_get(cache_dir: Path | None, key: str) -> dict | None:
    path = cache_dir / f"{key}.json" if cache_dir else None
    return json.loads(path.read_text()) if path and path.exists() else None


def cache_put(cache_dir: Path | None, key: str, record: dict) -> None:
    if cache_dir and record["status"] != "error":          # never cache a harness failure
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{key}.json").write_text(json.dumps(record, sort_keys=True))


# --- The run ------------------------------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_cases(suite: str) -> list[dict]:
    return W7.read_jsonl(COURSE / SUITES[suite]["cases"])


def run_suite(suite: str, agent: str, strict: bool = True, *, judge: str = "none", seed: int = 0,
              retries: int = 0, workers: int = 1, budget: float | None = None,
              cache_dir: Path | None = None, now=utc_now, cases: list[dict] | None = None) -> dict:
    """Run a suite and return the run artifact. Cases are admitted in file order until the budget runs out."""
    cases = cases if cases is not None else read_cases(suite)
    config = {"suite": suite, "agent": agent, "backend": "strict" if strict else "lax", "judge": judge,
              "seed": seed, "retries": retries, "budget_usd": budget}
    vers = versions(suite)
    run_id = "run-" + hashlib.sha256(json.dumps([config, vers], sort_keys=True).encode()).hexdigest()[:12]

    records: dict[str, dict] = {}
    to_run, reserved, stop_reason = [], 0.0, None
    for case in cases:
        key = cache_key(suite, case, agent, strict, judge, seed, retries)
        hit = cache_get(cache_dir, key)
        if hit is not None:
            records[case["case_id"]] = {**hit, "cached": True, "cost_usd": 0.0}
            continue
        need = RESERVE_PER_ATTEMPT * (1 + retries)
        if budget is not None and reserved + need > budget + 1e-9:
            stop_reason = f"budget ${budget:.4f} exhausted: {len(records) + len(to_run)} of {len(cases)} cases admitted"
            break
        reserved += need
        to_run.append((case, key))

    def work(item):
        case, key = item
        record = evaluate_case(suite, case, agent, strict, judge, seed, retries)
        cache_put(cache_dir, key, record)
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:          # map() keeps the input order
        for record in pool.map(work, to_run):
            records[record["case_id"]] = record
    ordered = [records[c["case_id"]] for c in cases if c["case_id"] in records]
    return {
        "schema_version": SCHEMA_VERSION, "run_id": run_id, "started_at": now(),
        "config": {**config, "workers": workers},
        "versions": vers,
        "environment": {"python": sys.version.split()[0], "platform": sys.platform},
        "expected_cases": len(cases), "completed_cases": len(ordered),
        "complete": len(ordered) == len(cases), "stop_reason": stop_reason,
        "summary": summarize(ordered), "cases": ordered,
    }


def summarize(records: list[dict]) -> dict:
    status = Counter(r["status"] for r in records)
    failed = Counter(c["severity"] for r in records for c in r["attempts"][0]["checks"] if not c["passed"])
    return {"status": {s: status[s] for s in ("pass", "fail", "flaky", "error")},
            "failed_checks_by_severity": {s: failed[s] for s in SEVERITIES},
            "safety": {k: sum(r["safety"][k] for r in records) for k in SAFETY_KEYS},
            "cache_hits": sum(r["cached"] for r in records),
            "cost_usd": round(sum(r["cost_usd"] for r in records), 6)}


def exit_code(artifact: dict) -> int:
    status = artifact["summary"]["status"]
    if not artifact["complete"] or status["error"]:
        return EXIT_INCOMPLETE
    return EXIT_FAIL if status["fail"] or status["flaky"] else EXIT_PASS


# --- Artifacts: write and verify --------------------------------------------------------------------

def write_artifact(artifact: dict, out: Path) -> None:
    """results.json holds the run. checksums.json lets a later job prove it was not altered or cut short."""
    out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    (out / "results.json").write_text(body)
    sums = {"run_id": artifact["run_id"], "files": {"results.json": hashlib.sha256(body.encode()).hexdigest()}}
    (out / "checksums.json").write_text(json.dumps(sums, indent=2, sort_keys=True) + "\n")


REQUIRED = {"schema_version", "run_id", "started_at", "config", "versions", "environment",
            "expected_cases", "completed_cases", "complete", "stop_reason", "summary", "cases"}


def verify_artifact(out: Path) -> list[str]:
    """Problems that make an artifact unusable as evidence. Empty means complete and intact."""
    try:
        sums = json.loads((out / "checksums.json").read_text())
        body = (out / "results.json").read_text()
    except FileNotFoundError as exc:
        return [f"missing file: {Path(exc.filename).name}"]
    except json.JSONDecodeError:
        return ["checksums.json is not valid JSON"]
    if hashlib.sha256(body.encode()).hexdigest() != sums["files"].get("results.json"):
        return ["results.json does not match its checksum"]
    run = json.loads(body)
    problems = [f"missing field: {k}" for k in sorted(REQUIRED - run.keys())]
    if problems:
        return problems
    if run["schema_version"] != SCHEMA_VERSION:
        problems.append(f"schema {run['schema_version']}, expected {SCHEMA_VERSION}")
    if sums["run_id"] != run["run_id"]:
        problems.append("checksums.json belongs to another run")
    ids = [c["case_id"] for c in run["cases"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate case IDs")
    if run["completed_cases"] != len(ids):
        problems.append(f"completed_cases says {run['completed_cases']}, the file holds {len(ids)}")
    if not run["complete"]:
        problems.append(f"incomplete run: {run['completed_cases']} of {run['expected_cases']} cases"
                        + (f" ({run['stop_reason']})" if run["stop_reason"] else ""))
    for key in ("case_set", "data_sha256", "policy_version", "code_sha256"):
        if not run["versions"].get(key):
            problems.append(f"no version recorded for {key}")
    return problems


# --- Flaky results -------------------------------------------------------------------------------------

def diagnose(verdicts: list[bool], fingerprints: set) -> str:
    """Which part of the pipeline varies between repeats of one case with every input held fixed."""
    if len(set(verdicts)) == 1:
        return "stable"
    if len(fingerprints) > 1:
        return "agent varies: the trace or the ledger differs between repeats"
    return "evaluator varies: same trace and ledger, different verdict"


def flake_report(suite: str, agent: str, strict: bool = True, judge: str = "simulated",
                 repeat: int = 20, seed: int = 0) -> list[dict]:
    """Repeat every case with seeds seed..seed+repeat-1. Report the cases whose verdict changed."""
    rows = []
    for case in read_cases(suite):
        runs = [run_attempt(suite, case, agent, strict, judge, seed + i, 0) for i in range(repeat)]
        verdicts = [attempt_passed(a) for a in runs]
        failing = Counter(c["check"] for a in runs for c in a["checks"] if not c["passed"])
        rows.append({"case_id": case["case_id"], "pass_rate": sum(verdicts) / repeat,
                     "fingerprints": len({a["fingerprint"] for a in runs}), "failing_checks": dict(failing),
                     "diagnosis": diagnose(verdicts, {a["fingerprint"] for a in runs})})
    return [r for r in rows if r["diagnosis"] != "stable"]


# --- Printing ------------------------------------------------------------------------------------------

MEANING = {0: "complete, every case passed", 1: "complete, some cases failed or were flaky",
           2: "incomplete or unusable", 3: "usage or configuration error"}


def print_run(run: dict, out: Path | None = None) -> None:
    c, v, s = run["config"], run["versions"], run["summary"]
    print(f"{run['run_id']}  suite={c['suite']} agent={c['agent']} backend={c['backend']} judge={c['judge']} "
          f"seed={c['seed']} retries={c['retries']} workers={c['workers']}")
    print(f"versions: {v['case_set']}, policy {v['policy_version']}, code {v['code_sha256'][:12]}")
    print(f"cases: {run['completed_cases']}/{run['expected_cases']} completed"
          + (f"  STOPPED: {run['stop_reason']}" if run["stop_reason"] else ""))
    print("status:  " + "  ".join(f"{k} {n}" for k, n in s["status"].items()))
    print("failed checks (first attempt): " + "  ".join(f"{k} {n}" for k, n in s["failed_checks_by_severity"].items()))
    print("safety:  " + "  ".join(f"{k} {n}" for k, n in s["safety"].items()))
    print(f"SIMULATED cost ${s['cost_usd']:.4f}, cache hits {s['cache_hits']}")
    for r in run["cases"]:
        if r["status"] != "pass":
            fails = [f"{x['check']}" for x in r["attempts"][0]["checks"] if not x["passed"]]
            seq = " -> ".join("pass" if attempt_passed(a) else "fail" for a in r["attempts"])
            print(f"  {r['status'].upper():<6}{r['case_id']}  ({r['slice']})  attempts: {seq}  first failed: {fails or r['attempts'][0]['error']}")
    code = exit_code(run)
    print(f"artifact: {out}" if out else "artifact: not written")
    print(f"exit {code}: {MEANING[code]}")


def print_flaky(rows: list[dict], repeat: int) -> None:
    print(f"{'case':<8}{'pass rate':>10}{'fingerprints':>14}  failing checks           diagnosis")
    for r in rows:
        checks = ", ".join(f"{k} x{n}" for k, n in r["failing_checks"].items())
        print(f"{r['case_id']:<8}{r['pass_rate']:>10.2f}{r['fingerprints']:>14}  {checks:<25}{r['diagnosis']}")
    print(f"{len(rows)} unstable cases across {repeat} repeats")


class Parser(argparse.ArgumentParser):
    """argparse exits 2 on bad arguments, which this runner reserves for incomplete runs. Use 3."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a suite and write results.json and checksums.json")
    flaky = sub.add_parser("flaky", help="repeat every case and report the unstable ones")
    for p in (run, flaky):
        p.add_argument("--suite", choices=list(SUITES), default="tools")
        p.add_argument("--agent", default="v2")
        p.add_argument("--backend", choices=["strict", "lax"], default="strict")
        p.add_argument("--seed", type=int, default=0)
    run.add_argument("--judge", choices=["none", "simulated"], default="none")
    run.add_argument("--retries", type=int, default=0)
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--budget", type=float, default=None, help="SIMULATED dollars")
    run.add_argument("--cache", type=Path, default=None)
    run.add_argument("--out", type=Path, required=True)
    flaky.add_argument("--repeat", type=int, default=20)
    verify = sub.add_parser("verify", help="check an artifact is complete and intact")
    verify.add_argument("out", type=Path)
    sub.add_parser("pins", help="show each pinned input and whether it still matches")
    args = parser.parse_args(argv)

    if args.command == "pins":
        for suite in SUITES:
            problems = check_pins(suite)
            print(f"{suite}: " + ("all inputs match their pins" if not problems else "; ".join(problems)))
        return EXIT_PASS
    if args.command == "verify":
        problems = verify_artifact(args.out)
        for p in problems:
            print(f"  PROBLEM {p}")
        if problems:
            print(f"exit {EXIT_INCOMPLETE}: {MEANING[EXIT_INCOMPLETE]}")
            return EXIT_INCOMPLETE
        run_data = json.loads((args.out / "results.json").read_text())
        code = exit_code(run_data)
        print(f"{run_data['run_id']}: complete and intact, {run_data['completed_cases']} cases")
        print(f"exit {code}: {MEANING[code]}")
        return code
    if args.agent not in SUITES[args.suite]["agents"]:
        parser.error(f"agent {args.agent} is not in suite {args.suite}: {SUITES[args.suite]['agents']}")
    if args.command == "run" and (args.workers < 1 or args.retries < 0 or (args.budget or 0) < 0):
        parser.error("--workers must be at least 1, --retries and --budget at least 0")
    problems = check_pins(args.suite)
    if problems:
        parser.error("pinned inputs changed, bump the version and the pin: " + "; ".join(problems))
    strict = args.backend == "strict"
    if args.command == "flaky":
        print_flaky(flake_report(args.suite, args.agent, strict, repeat=args.repeat, seed=args.seed), args.repeat)
        return EXIT_PASS
    artifact = run_suite(args.suite, args.agent, strict, judge=args.judge, seed=args.seed, retries=args.retries,
                         workers=args.workers, budget=args.budget, cache_dir=args.cache)
    write_artifact(artifact, args.out)
    print_run(artifact, args.out)
    return exit_code(artifact)


if __name__ == "__main__":
    sys.exit(main())
