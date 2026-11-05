"""Week 12 lab: a machine-readable release policy and the gate that applies it.

Usage, from new_course/:
    python3 weeks/week-12-release-gates/handson/lab.py scenarios
    python3 weeks/week-12-release-gates/handson/lab.py run --agent v2.3 --out RUN_DIR
    python3 weeks/week-12-release-gates/handson/lab.py gate --baseline BASE_DIR --candidate CAND_DIR --out REPORT_DIR
    python3 weeks/week-12-release-gates/handson/lab.py canary

`run` evaluates one agent version twice with Week 11's runner and writes RUN_DIR/release/
(strict backend) and RUN_DIR/safety_probe/ (lax backend). `gate` reads two such folders and
the policy in dataset/release-policy-v1.json, and decides.

Exit codes of `gate`:
    0  SHIP   every rule passed on complete, intact, comparable evidence
    1  BLOCK  a hard, quality or regression rule failed
    2  HOLD   evidence is missing or invalid, or a soft rule failed
    3  usage or configuration error (bad arguments, an invalid policy file): no decision

`canary` applies the policy's canary stage to SIMULATED metrics: 0 PROMOTE, 1 ROLLBACK, 2 EXTEND.
Thresholds in the policy are ILLUSTRATIVE. No model is called anywhere in this lab.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.release_candidates import CANDIDATES  # noqa: E402

DATA = HERE.parent / "dataset"
POLICY = DATA / "release-policy-v1.json"
CANARY = DATA / "canary-metrics-v1.json"
RUNS = HERE / "runs"
EXIT = {"SHIP": 0, "BLOCK": 1, "HOLD": 2}
EXIT_USAGE = 3
RISK_ORDER = ("critical", "high", "normal")


def load_week_lab(folder: str, name: str):
    """Week 12 drives Week 11's runner unchanged, so it loads its lab (Week 6's pattern)."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W11 = load_week_lab("week-11-evaluation-harness-and-ci", "week11_lab_for_w12")


def register_candidates(w11) -> None:
    """Teach this copy of Week 11's runner the candidate agents, and hash their module into every run."""
    w11.W7.AGENTS.update(CANDIDATES)
    w11.SUITES["tools"]["agents"] += [a for a in CANDIDATES if a not in w11.SUITES["tools"]["agents"]]
    if "shared/release_candidates.py" not in w11.SUITES["tools"]["code"]:
        w11.SUITES["tools"]["code"].append("shared/release_candidates.py")


register_candidates(W11)


# --- The policy -----------------------------------------------------------------------------------

class PolicyError(Exception):
    """The policy file itself is unusable. The gate refuses to decide (exit 3)."""


RULE_GROUPS = ("hard_gates", "quality_gates", "regression_gates", "soft_gates")


def load_policy(path: Path = POLICY) -> dict:
    """Read the policy and reject one the gate could misread. A typo here must not become a pass."""
    try:
        policy = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot read policy {path}: {exc}") from exc
    problems = [f"missing {k}" for k in ("version", "artifact_schema", "runs", *RULE_GROUPS) if k not in policy]
    for group in RULE_GROUPS:
        for rule in policy.get(group, []):
            runs = rule.get("runs") or [rule.get("run")]
            if not rule.get("id") or not rule.get("metric") or any(r not in policy.get("runs", {}) for r in runs):
                problems.append(f"{group}: rule {rule.get('id')} needs an id, a metric and known runs")
            limits = {"max", "min", "max_ratio_to_baseline", "max_decline_by_risk"} & rule.keys()
            if len(limits) != 1:
                problems.append(f"{group}: rule {rule.get('id')} needs exactly one limit, has {sorted(limits)}")
    if problems:
        raise PolicyError("; ".join(problems))
    policy["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return policy


# --- Producing evidence ---------------------------------------------------------------------------

def produce(agent: str, out: Path, policy: dict, *, now=W11.utc_now, budget: float | None = None,
            cases: list[dict] | None = None) -> dict:
    """Run every evaluation the policy asks for, one folder per run name, with Week 11's runner."""
    artifacts = {}
    for name, spec in policy["runs"].items():
        cfg = spec["config"]
        run = W11.run_suite(cfg["suite"], agent, cfg["backend"] == "strict", judge=cfg["judge"],
                            retries=cfg["retries"], budget=budget if name == "release" else None,
                            now=now, cases=cases)
        W11.write_artifact(run, out / name)
        artifacts[name] = run
    return artifacts


def rewrite_artifact(run_dir: Path, edit) -> None:
    """SIMULATED: rewrite a run as another producer would have written it, with a valid checksum."""
    run = json.loads((run_dir / "results.json").read_text())
    edit(run)
    W11.write_artifact(run, run_dir)


# --- Reading evidence ------------------------------------------------------------------------------

def load_run(version_dir: Path, name: str, policy: dict) -> tuple[dict | None, list[str]]:
    """One run, or None with the reasons it cannot be used. Never a partial or unverified run."""
    where = f"{version_dir.name}/{name}"
    problems = W11.verify_artifact(version_dir / name)
    if problems:
        return None, [f"{where}: {p}" for p in problems]
    run = json.loads((version_dir / name / "results.json").read_text())
    if run["schema_version"] != policy["artifact_schema"]:
        return None, [f"{where}: schema {run['schema_version']}, policy reads {policy['artifact_schema']}"]
    wrong = [f"{where}: config {k} is {run['config'].get(k)!r}, policy needs {v!r}"
             for k, v in policy["runs"][name]["config"].items() if run["config"].get(k) != v]
    return (None, wrong) if wrong else (run, [])


def comparability(base: dict, cand: dict, name: str) -> list[str]:
    """A paired comparison needs the same cases, data and policy on both sides, and every case the suite has."""
    problems = [f"{name}: baseline and candidate differ in {k}" for k in
                ("case_set", "data_sha256", "dataset_version", "policy_version")
                if base["versions"].get(k) != cand["versions"].get(k)]
    suite_ids = {c["case_id"] for c in W11.read_cases(cand["config"]["suite"])}
    for side, run in (("baseline", base), ("candidate", cand)):
        ids = {c["case_id"] for c in run["cases"]}
        if ids != suite_ids:
            problems.append(f"{name}: {side} has {len(ids)} of the suite's {len(suite_ids)} cases, "
                            f"missing {sorted(suite_ids - ids)}")
    return problems


class Missing(Exception):
    """A metric the gate could not read. Never treated as zero."""


def first_checks(case: dict) -> dict[str, dict]:
    return {c["check"]: c for c in case["attempts"][0]["checks"]}


def read_summary(run: dict, path: str) -> tuple[float, list[str]]:
    """A summary count, plus the case IDs behind it as evidence pointers."""
    node = run["summary"]
    try:
        for key in path.split("."):
            node = node[key]
    except (KeyError, TypeError):
        raise Missing(f"summary.{path} not in run {run['run_id']}") from None
    if not isinstance(node, (int, float)) or isinstance(node, bool):
        raise Missing(f"summary.{path} is {node!r}, not a number")
    group, _, key = path.partition(".")
    if group == "safety":
        cases = [c["case_id"] for c in run["cases"] if c.get("safety", {}).get(key)]
    elif group == "failed_checks_by_severity":
        cases = [c["case_id"] for c in run["cases"]
                 if any(not x["passed"] and x["severity"] == key for x in c["attempts"][0]["checks"])]
    elif group == "status":
        cases = [c["case_id"] for c in run["cases"] if c["status"] == key]
    else:
        cases = []
    return node, cases


def case_rate(run: dict, checks: list[str]) -> tuple[float, list[str]]:
    """Share of cases whose first attempt passed every named check. A case without one is Missing."""
    failing = []
    for case in run["cases"]:
        mine = first_checks(case)
        absent = [c for c in checks if c not in mine]
        if absent:
            raise Missing(f"{case['case_id']} has no {absent} check in run {run['run_id']}")
        if not all(mine[c]["passed"] for c in checks):
            failing.append(case["case_id"])
    if not run["cases"]:
        raise Missing(f"run {run['run_id']} has no cases")
    return 1 - len(failing) / len(run["cases"]), failing


def slice_risks(suite: str) -> dict[str, str]:
    """A slice takes the highest risk of its cases, read from the pinned case file."""
    risks = defaultdict(set)
    for case in W11.read_cases(suite):
        risks[case["slice"]].add(case["risk"])
    return {s: next(r for r in RISK_ORDER if r in rs) for s, rs in risks.items()}


def flips(base: dict, cand: dict) -> dict[str, list[str]]:
    """Paired by case ID. Only a first-attempt pass counts, so a flaky case counts as a fail."""
    before = {c["case_id"]: c["status"] == "pass" for c in base["cases"]}
    after = {c["case_id"]: c["status"] == "pass" for c in cand["cases"]}
    return {"pass_to_fail": sorted(i for i in before if before[i] and not after[i]),
            "fail_to_pass": sorted(i for i in before if not before[i] and after[i])}


def slice_regressions(base: dict, cand: dict, max_decline: dict[str, float]) -> list[dict]:
    """Per slice: pass rates before and after on the same cases, the decline, and the case IDs that flipped."""
    risk = slice_risks(cand["config"]["suite"])
    by_slice = defaultdict(lambda: [[], []])
    for side, run in enumerate((base, cand)):
        for c in run["cases"]:
            by_slice[c["slice"]][side].append(c)
    flipped = set(flips(base, cand)["pass_to_fail"])
    rows = []
    for name, (b, c) in sorted(by_slice.items()):
        rate_b = sum(x["status"] == "pass" for x in b) / len(b)
        rate_c = sum(x["status"] == "pass" for x in c) / len(c)
        tolerance = max_decline[risk[name]]
        rows.append({"slice": name, "risk": risk[name], "cases": len(c), "baseline": rate_b, "candidate": rate_c,
                     "decline": round(rate_b - rate_c, 4), "tolerance": tolerance,
                     "breached": rate_b - rate_c > tolerance + 1e-9,
                     "flipped": sorted(x["case_id"] for x in c if x["case_id"] in flipped)})
    return rows


# --- Applying the rules ----------------------------------------------------------------------------

def rule_result(rule: dict, group: str, values: list, failed: bool, missing: list[str], cases: list[str],
                detail: str) -> dict:
    """Fail closed: a missing value makes the rule MISSING, and MISSING holds the release."""
    result = "FAIL" if failed else ("MISSING" if missing else "PASS")
    effect = {"PASS": None, "MISSING": "HOLD",
              "FAIL": "HOLD" if group == "soft_gates" else "BLOCK"}[result]
    limit = {k: rule[k] for k in ("max", "min", "max_ratio_to_baseline", "max_decline_by_risk") if k in rule}
    return {"id": rule["id"], "group": group, "result": result, "effect": effect, "values": values,
            "limit": limit, "cases": sorted(set(cases)), "missing": missing,
            "override": rule.get("override") if result == "FAIL" else None, "detail": detail}


def apply_rule(rule: dict, group: str, base: dict, cand: dict, paired: dict) -> dict:
    """One rule against the candidate's runs (and the baseline's, for paired rules)."""
    runs = rule.get("runs") or [rule["run"]]
    metric = rule["metric"]
    values, cases, missing, failed, detail = [], [], [], False, ""
    for name in runs:
        run = cand.get(name)
        try:
            if run is None:
                raise Missing(f"candidate {name} run is unusable")
            if "max_ratio_to_baseline" in rule or "max_decline_by_risk" in rule:
                if not paired.get(name):
                    raise Missing(f"{name}: baseline and candidate cannot be paired")
            if "slice_pass_rate" in metric:
                rows = slice_regressions(base[name], run, rule["max_decline_by_risk"])
                bad = [r for r in rows if r["breached"]]
                values.append({r["slice"]: round(r["candidate"] - r["baseline"], 4) for r in rows if r["decline"]})
                cases += [i for r in bad for i in r["flipped"]]
                failed |= bool(bad)
                detail = "; ".join(f"{r['slice']} ({r['risk']}) {r['baseline']:.0%} -> {r['candidate']:.0%}, "
                                   f"tolerance {r['tolerance']:.0%}" for r in bad)
                continue
            if "case_rate" in metric:
                value, behind = case_rate(run, metric["case_rate"])
            else:
                value, behind = read_summary(run, metric["summary"])
            if "max_ratio_to_baseline" in rule:
                base_value, _ = read_summary(base[name], metric["summary"])
                ratio = value / base_value if base_value else float("inf")
                values.append({"run": name, "value": value, "baseline": base_value, "ratio": round(ratio, 3)})
                failed |= ratio > rule["max_ratio_to_baseline"]
                continue
            values.append({"run": name, "value": round(value, 4)})
            breach = value > rule["max"] if "max" in rule else value < rule["min"]
            if breach:
                failed, cases = True, cases + behind
        except Missing as exc:
            missing.append(str(exc))
    return rule_result(rule, group, values, failed, missing, cases, detail)


def gate(baseline_dir: Path, candidate_dir: Path, policy: dict | None = None, *, now=W11.utc_now) -> dict:
    """Decide SHIP, BLOCK or HOLD for a candidate against the baseline, under the policy."""
    policy = policy or load_policy()
    base, cand, problems, paired = {}, {}, [], {}
    for name in policy["runs"]:
        for side, store, folder in (("baseline", base, baseline_dir), ("candidate", cand, candidate_dir)):
            store[name], why = load_run(folder, name, policy)
            problems += why
        if base[name] and cand[name]:
            why = comparability(base[name], cand[name], name)
            problems += why
            paired[name] = not why
    rules = [apply_rule(rule, group, base, cand, paired) for group in RULE_GROUPS for rule in policy[group]]
    effects = {r["effect"] for r in rules} | ({policy["evidence"]["on_problem"]} if problems else set())
    verdict = next(v for v in policy["precedence"] if v in effects or v == "SHIP")
    release = (base.get("release"), cand.get("release"))
    return {
        "policy": {"id": policy["policy_id"], "version": policy["version"], "sha256": policy["sha256"]},
        "decided_at": now(), "verdict": verdict, "exit_code": EXIT[verdict],
        "baseline": side_info(baseline_dir, base), "candidate": side_info(candidate_dir, cand),
        "evidence_problems": problems, "rules": rules,
        "flips": flips(*release) if all(release) and paired.get("release") else None,
    }


def side_info(folder: Path, runs: dict) -> dict:
    agents = {r["config"]["agent"] for r in runs.values() if r}
    return {"dir": folder.as_posix(), "agent": agents.pop() if len(agents) == 1 else None,
            "runs": {name: r["run_id"] if r else None for name, r in runs.items()}}


# --- Reports -----------------------------------------------------------------------------------------

def reasons(decision: dict) -> list[str]:
    out = [f"evidence: {p}" for p in decision["evidence_problems"]]
    for r in decision["rules"]:
        if r["result"] == "FAIL":
            why = r["detail"] or ", ".join(f"{v.get('run')} {v.get('ratio', v.get('value'))}" for v in r["values"]
                                          if isinstance(v, dict) and "run" in v)
            out.append(f"{r['id']} FAIL ({why})" + (f" cases {r['cases']}" if r["cases"] else "")
                       + (f", override: {r['override']}" if r["override"] else ""))
        elif r["result"] == "MISSING":
            out.append(f"{r['id']} MISSING ({r['missing'][0]})")
    return out


def render_markdown(decision: dict) -> str:
    """The same decision for people: verdict first, then every rule with its evidence."""
    d, cand, base = decision, decision["candidate"], decision["baseline"]
    lines = [f"# Release decision: {cand['agent'] or cand['dir']} against {base['agent'] or base['dir']}", "",
             f"**Verdict: {d['verdict']}** (exit {d['exit_code']}). Policy {d['policy']['id']} {d['policy']['version']} "
             f"(sha256 {d['policy']['sha256'][:12]}), decided {d['decided_at']}.", "",
             "| Run | Baseline | Candidate |", "| --- | --- | --- |"]
    lines += [f"| {n} | {base['runs'][n] or 'unusable'} | {cand['runs'][n] or 'unusable'} |" for n in base["runs"]]
    if d["evidence_problems"]:
        lines += ["", "## Evidence problems", ""] + [f"- {p}" for p in d["evidence_problems"]]
    lines += ["", "## Rules", "", "| Rule | Group | Result | Effect | Values | Cases |", "| --- | --- | --- | --- | --- | --- |"]
    for r in d["rules"]:
        vals = "; ".join(json.dumps(v, sort_keys=True) for v in r["values"]) or "; ".join(r["missing"])
        lines.append(f"| {r['id']} | {r['group']} | {r['result']} | {r['effect'] or ''} | {vals} | "
                     f"{', '.join(r['cases'])} |")
    if d["flips"]:
        lines += ["", f"Paired release run: pass to fail {d['flips']['pass_to_fail'] or 'none'}, "
                      f"fail to pass {d['flips']['fail_to_pass'] or 'none'}."]
    return "\n".join(lines) + "\n"


def write_decision(decision: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "decision.json").write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")
    (out / "decision.md").write_text(render_markdown(decision))


def print_decision(decision: dict) -> None:
    c, b = decision["candidate"], decision["baseline"]
    print(f"{c['agent'] or c['dir']} vs {b['agent'] or b['dir']}: {decision['verdict']} (exit {decision['exit_code']})")
    for line in reasons(decision):
        print(f"  {line}")
    if decision["flips"]:
        print(f"  flips: pass->fail {decision['flips']['pass_to_fail']}, fail->pass {decision['flips']['fail_to_pass']}")


# --- Scenarios: every verdict, from real runs ------------------------------------------------------

def build_scenarios(out: Path, policy: dict, now=W11.utc_now) -> list[tuple[str, Path, str]]:
    """Run the baseline and every candidate, then derive the broken-evidence variants from v2.1's runs."""
    for agent in ("v2", *CANDIDATES):
        produce(agent, out / agent, policy, now=now)
    produce("v2.1", out / "v2.1-budget", policy, now=now, budget=0.02)
    produce("v2.3", out / "v2.3-tampered", policy, now=now)
    probe = out / "v2.3-tampered" / "safety_probe" / "results.json"
    probe.write_text(probe.read_text().replace('"unauthorized_refunds": 1', '"unauthorized_refunds": 0'))
    produce("v2.1", out / "v2.1-no-probe", policy, now=now)
    for f in (out / "v2.1-no-probe" / "safety_probe").iterdir():
        f.unlink()
    (out / "v2.1-no-probe" / "safety_probe").rmdir()
    produce("v2.1", out / "v2.1-other-policy", policy, now=now)
    rewrite_artifact(out / "v2.1-other-policy" / "release", lambda r: r["versions"].update(policy_version="2026-02"))
    return [
        ("passing candidate", out / "v2.1", "names the order in every reply"),
        ("slice regression", out / "v2.2", "denies refunds over $1,000"),
        ("one unauthorized refund", out / "v2.3", "trusts a named card as proof of ownership"),
        ("soft gate", out / "v2.4", "a second policy lookup per case"),
        ("budget-stopped run", out / "v2.1-budget", "release run stopped after 6 of 30 cases"),
        ("tampered artifact", out / "v2.3-tampered", "probe edited after the run to hide the refund"),
        ("missing probe", out / "v2.1-no-probe", "safety_probe folder absent"),
        ("other policy version", out / "v2.1-other-policy", "SIMULATED: release run against policy 2026-02"),
    ]


def print_scenarios(rows: list[tuple[str, Path, str]], baseline: Path, policy: dict, now=W11.utc_now) -> list[dict]:
    decisions = []
    print(f"{'scenario':<26}{'candidate':<20}{'verdict':<8}exit  first reason")
    for label, folder, _what in rows:
        d = gate(baseline, folder, policy, now=now)
        decisions.append(d)
        first = (reasons(d) or ["every rule passed"])[0]
        print(f"{label:<26}{folder.name:<20}{d['verdict']:<8}{d['exit_code']:<6}{first[:110]}")
    return decisions


# --- Canary ----------------------------------------------------------------------------------------

def canary_decision(observation: dict, policy: dict) -> dict:
    """PROMOTE, EXTEND or ROLLBACK for one SIMULATED canary observation."""
    stage, canary, control = policy["canary"], observation["canary"], observation["control"]
    enough = canary["requests"] >= stage["min_requests"] and canary["refund_attempts"] >= stage["min_refund_attempts"]
    breaches, unjudged = [], []
    for g in stage["guardrails"]:
        value, base = canary[g["metric"]], control[g["metric"]]
        if g["kind"] == "hard":
            if value > g["max"]:
                breaches.append(f"{g['id']}: {value}, limit {g['max']}")
            continue
        limit = (base + g["max_increase_over_control"] if "max_increase_over_control" in g
                 else base * g["max_ratio_to_control"])
        if not enough:
            unjudged.append(g["id"])
        elif value > limit + 1e-9:
            breaches.append(f"{g['id']}: {value}, limit {limit:.3f} (control {base})")
    if breaches:
        decision = "ROLLBACK"
    elif not enough:
        decision = "ROLLBACK" if observation["hours"] >= stage["max_hours"] else "EXTEND"
    else:
        decision = "PROMOTE"
    return {"id": observation["id"], "candidate": observation["candidate"], "decision": decision,
            "exit_code": {"PROMOTE": 0, "ROLLBACK": 1, "EXTEND": 2}[decision], "breaches": breaches,
            "unjudged": unjudged, "volume": f"{canary['requests']} requests, {canary['refund_attempts']} refund attempts"}


def print_canary(policy: dict, only: str | None = None) -> list[dict]:
    data = json.loads(CANARY.read_text())
    print(f"SIMULATED canary metrics, traffic share {policy['canary']['traffic_share']:.0%}, "
          f"minimum {policy['canary']['min_requests']} requests and {policy['canary']['min_refund_attempts']} refund attempts")
    out = []
    for obs in data["observations"]:
        if only and obs["id"] != only:
            continue
        d = canary_decision(obs, policy)
        out.append(d)
        why = "; ".join(d["breaches"]) or (f"too little volume to judge {d['unjudged']}" if d["unjudged"] else "no breach")
        print(f"{d['id']:<14}{d['decision']:<9}exit {d['exit_code']}  {d['volume']}: {why}")
    return out


# --- Command line ----------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = W11.Parser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="evaluate one agent version for every run the policy needs")
    run.add_argument("--agent", required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--budget", type=float, default=None, help="SIMULATED dollars, release run only")
    g = sub.add_parser("gate", help="decide SHIP, BLOCK or HOLD")
    g.add_argument("--baseline", type=Path, required=True)
    g.add_argument("--candidate", type=Path, required=True)
    g.add_argument("--out", type=Path, default=None, help="write decision.json and decision.md here")
    sc = sub.add_parser("scenarios", help="build every scenario from real runs and gate each one")
    sc.add_argument("--out", type=Path, default=RUNS / "scenarios")
    cn = sub.add_parser("canary", help="apply the canary stage to the SIMULATED metrics")
    cn.add_argument("--observation", default=None)
    for p in (run, g, sc, cn):
        p.add_argument("--policy", type=Path, default=POLICY)
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
    except PolicyError as exc:
        parser.error(str(exc))

    if args.command == "run":
        if args.agent not in W11.SUITES["tools"]["agents"]:
            parser.error(f"unknown agent {args.agent}: {W11.SUITES['tools']['agents']}")
        for name, art in produce(args.agent, args.out, policy, budget=args.budget).items():
            s = art["summary"]
            print(f"{name:<13}{art['run_id']}  {art['completed_cases']}/{art['expected_cases']} cases, "
                  f"pass {s['status']['pass']}, critical {s['failed_checks_by_severity']['critical']}, "
                  f"safety {sum(s['safety'].values())}  -> {args.out / name}")
        return 0
    if args.command == "gate":
        decision = gate(args.baseline, args.candidate, policy)
        print_decision(decision)
        if args.out:
            write_decision(decision, args.out)
            print(f"  report: {args.out / 'decision.json'}, {args.out / 'decision.md'}")
        return decision["exit_code"]
    if args.command == "scenarios":
        rows = build_scenarios(args.out, policy)
        print_scenarios(rows, args.out / "v2", policy)
        return 0
    print_canary(policy, args.observation)
    return 0


if __name__ == "__main__":
    sys.exit(main())
