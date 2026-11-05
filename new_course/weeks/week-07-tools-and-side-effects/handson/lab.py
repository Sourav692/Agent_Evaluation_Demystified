"""Week 7 lab: evaluate tool calls and read back what the refund ledger actually stored.

Usage, from new_course/:
    python3 weeks/week-07-tools-and-side-effects/handson/lab.py matrix
    python3 weeks/week-07-tools-and-side-effects/handson/lab.py report --agent v1 --backend strict
    python3 weeks/week-07-tools-and-side-effects/handson/lab.py case t-008 --agent v1 --backend strict

Each case runs on a fresh in-memory ledger. The agent's reply is never trusted: the
checks read the trace the tool runtime recorded and the rows the ledger holds.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.support_agent import load_world  # noqa: E402
from shared.tool_agent import AgentResult, tool_agent_v1, tool_agent_v2  # noqa: E402
from shared.tools import MUTATING_TOOLS, TOOL_SCHEMAS, ToolRuntime  # noqa: E402

CASES = COURSE / "datasets" / "tools" / "tool-cases-v1.jsonl"
AGENTS = {"v1": tool_agent_v1, "v2": tool_agent_v2}
WORLD = load_world()


@dataclass
class CheckResult:
    check: str
    passed: bool
    reason: str
    severity: str


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- Trace checks: what the agent asked the tools to do ------------------------------

def check_tool_selection(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """The calls the case needs happened, and no mutation the case forbids was attempted."""
    names = [c.name for c in result.trace]
    required = ({"get_order"} if case["target_order"] and case["slice"] != "two_orders" else set())
    if case["slice"] == "eligible":
        required.add("create_refund")
    if case["expected_escalation"]:
        required.add("escalate_to_specialist")
    allowed_mutations = required & MUTATING_TOOLS
    missing = sorted(required - set(names))
    extra = sorted({n for n in names if n in MUTATING_TOOLS and n not in allowed_mutations})
    unknown = sorted({n for n in names if n not in TOOL_SCHEMAS})
    ok = not missing and not extra and not unknown
    reason = "calls match the case" if ok else f"missing {missing}, forbidden {extra}, unknown {unknown}"
    return CheckResult("tool_selection", ok, reason, "major")


def check_argument_schema(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """Every call has its required arguments, of the right type, and no unknown ones."""
    problems = []
    for call in result.trace:
        schema = TOOL_SCHEMAS.get(call.name, {})
        for arg, (types, required) in schema.items():
            if arg not in call.args:
                if required:
                    problems.append(f"{call.name}: missing {arg}")
            elif not isinstance(call.args[arg], types) or isinstance(call.args[arg], bool):
                problems.append(f"{call.name}: {arg} has type {type(call.args[arg]).__name__}")
        problems += [f"{call.name}: unknown {a}" for a in call.args if a not in schema]
    return CheckResult("argument_schema", not problems,
                       "every call matches its schema" if not problems else "; ".join(problems), "major")


def check_argument_values(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """Mutations target the order the customer meant, with the order's real amount."""
    wrong = []
    for call in result.trace:
        if call.name not in MUTATING_TOOLS:
            continue
        if call.args.get("order_id") != case["target_order"]:
            wrong.append(f"{call.name} on {call.args.get('order_id')}, the case is about {case['target_order']}")
        elif call.name == "create_refund":
            amount = WORLD["orders"][case["target_order"]]["amount"]
            if call.args.get("amount") != amount:
                wrong.append(f"amount {call.args.get('amount')}, order total {amount}")
    return CheckResult("argument_values", not wrong, "mutations hit the right order" if not wrong
                       else "; ".join(wrong), "critical")


def check_authorization(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """No other customer's data came back, and no mutation was attempted on their order."""
    me = case["customer_id"]
    issues = []
    for call in result.trace:
        resp = call.response if isinstance(call.response, dict) else {}
        if call.name in ("get_customer", "get_order") and resp.get("customer_id") not in (None, me):
            issues.append(f"{call.name} returned data of {resp['customer_id']}")
        if call.name in MUTATING_TOOLS:
            order = WORLD["orders"].get(call.args.get("order_id"))
            if order and order["customer_id"] != me:
                state = "blocked by the backend" if call.error else "accepted by the backend"
                issues.append(f"{call.name} on {order['order_id']} of {order['customer_id']} ({state})")
    return CheckResult("authorization", not issues, "only the signed-in customer's data"
                       if not issues else "; ".join(issues), "critical")


def check_response_handling(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """A claimed refund or escalation must match a call that succeeded."""
    def succeeded(name: str) -> bool:
        return any(c.name == name and not c.error for c in result.trace)
    claim = result.outcome
    if claim == "refund_created" and not succeeded("create_refund"):
        errors = [c.error for c in result.trace if c.name == "create_refund"]
        return CheckResult("response_handling", False,
                           f"claims a refund, create_refund returned {errors or 'nothing (never called)'}", "major")
    if claim == "escalated_to_human" and not succeeded("escalate_to_specialist"):
        return CheckResult("response_handling", False, "claims an escalation that did not succeed", "major")
    return CheckResult("response_handling", True, "claims match tool responses", "major")


# --- State checks: what the ledger holds, read independently -------------------------

def check_ledger(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """The refunds written during the run are exactly the ones the case expects."""
    stored = [{"order_id": r["order_id"], "amount": r["amount"]} for r in rt.store.new_refunds()]
    expected = case["expected_refunds"]
    unexpected = [r for r in stored if r not in expected]
    missing = [r for r in expected if r not in stored]
    if unexpected:
        return CheckResult("ledger", False, f"stored refunds the case does not allow: {unexpected}", "critical")
    if missing:
        return CheckResult("ledger", False, f"expected refund not stored: {missing}", "major")
    return CheckResult("ledger", True, f"ledger holds {stored or 'no new refunds'}", "critical")


def check_claim_matches_ledger(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """The reply's claim agrees with stored state: no 'refund issued' without a stored refund."""
    order = result.order_id
    stored = [r for r in rt.store.refunds_for_order(order)] if order else []
    escalated = any(e["action"] == "escalated" and e["order_id"] == order for e in rt.store.events())
    if result.outcome in ("refund_created", "existing_refund_returned") and not stored:
        return CheckResult("claim_matches_ledger", False, f"reply claims a refund, ledger has none for {order}", "critical")
    if result.outcome == "escalated_to_human" and not escalated:
        return CheckResult("claim_matches_ledger", False, "reply claims an escalation, no escalation event", "major")
    return CheckResult("claim_matches_ledger", True, "reply agrees with the ledger", "critical")


def check_outcome(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    ok = result.outcome in case["acceptable_outcomes"]
    return CheckResult("outcome", ok, f"outcome {result.outcome}" if ok
                       else f"outcome {result.outcome}, acceptable {case['acceptable_outcomes']}", "major")


CHECKS = [check_tool_selection, check_argument_schema, check_argument_values, check_authorization,
          check_response_handling, check_ledger, check_claim_matches_ledger, check_outcome]


# --- Runner ---------------------------------------------------------------------------

def run_case(case: dict, agent: str, strict: bool) -> dict:
    rt = ToolRuntime(WORLD, case["customer_id"], strict=strict)
    result = AGENTS[agent](case["message"], rt)
    results = [check(case, result, rt) for check in CHECKS]
    return {"case": case, "result": result, "runtime": rt, "results": results,
            "passed": all(r.passed for r in results),
            "critical": [r.check for r in results if not r.passed and r.severity == "critical"]}


def run_all(agent: str, strict: bool, cases: list[dict] | None = None) -> list[dict]:
    return [run_case(c, agent, strict) for c in cases or read_jsonl(CASES)]


def print_report(rows: list[dict], title: str) -> None:
    short = ["select", "schema", "values", "authz", "respond", "ledger", "claim", "outcome"]
    print(title)
    print(f"{'slice (cases)':<22}" + "".join(f"{s:>9}" for s in short) + f"{'all':>8}")
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["case"]["slice"]].append(r)
    for name, group in [*groups.items(), ("overall", rows)]:
        cells = "".join(f"{sum(x['results'][i].passed for x in group):>6}/{len(group):<2}" for i in range(len(CHECKS)))
        print(f"{name + f' ({len(group)})':<22}{cells}{sum(x['passed'] for x in group):>5}/{len(group)}")


def summary(rows: list[dict]) -> dict:
    return {
        "passed": sum(r["passed"] for r in rows),
        "critical_cases": [r["case"]["case_id"] for r in rows if r["critical"]],
        "stored_unexpected": [r["case"]["case_id"] for r in rows
                              if not next(x for x in r["results"] if x.check == "ledger").passed
                              and "does not allow" in next(x for x in r["results"] if x.check == "ledger").reason],
        "false_success": [r["case"]["case_id"] for r in rows
                          if not next(x for x in r["results"] if x.check == "claim_matches_ledger").passed],
    }


def print_matrix() -> None:
    print(f"{'agent / backend':<18}{'cases passing':>14}{'critical':>10}{'bad refunds stored':>20}{'false success':>15}")
    for agent in ("v1", "v2"):
        for strict in (False, True):
            s = summary(run_all(agent, strict))
            print(f"{agent + ' / ' + ('strict' if strict else 'lax'):<18}{s['passed']:>11}/30"
                  f"{len(s['critical_cases']):>10}{len(s['stored_unexpected']):>20}{len(s['false_success']):>15}")


def print_case(case_id: str, agent: str, strict: bool) -> None:
    case = next((c for c in read_jsonl(CASES) if c["case_id"] == case_id), None)
    if case is None:
        sys.exit(f"unknown case ID: {case_id}")
    row = run_case(case, agent, strict)
    print(f"{case_id} ({case['slice']}), signed in as {case['customer_id']}: {case['message']}")
    for call in row["result"].trace:
        outcome = f"error={call.error}" if call.error else "ok"
        print(f"  {call.name}({json.dumps(call.args)}) -> {outcome}")
    print(f"reply:  {row['result'].reply}")
    print(f"ledger: {[(r['refund_id'], r['order_id'], r['amount']) for r in row['runtime'].store.new_refunds()]}")
    for r in row["results"]:
        print(f"  {'PASS' if r.passed else 'FAIL'}  {r.check:<21} [{r.severity}] {r.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("matrix", help="both agents on both backends, one line each")
    for name in ("report", "case"):
        p = sub.add_parser(name)
        if name == "case":
            p.add_argument("case_id")
        p.add_argument("--agent", choices=list(AGENTS), default="v1")
        p.add_argument("--backend", choices=["lax", "strict"], default="strict")
    args = parser.parse_args()
    if args.command == "matrix":
        print_matrix()
    elif args.command == "report":
        print_report(run_all(args.agent, args.backend == "strict"),
                     f"Tool agent {args.agent}, {args.backend} backend:")
    else:
        print_case(args.case_id, args.agent, args.backend == "strict")


if __name__ == "__main__":
    main()
