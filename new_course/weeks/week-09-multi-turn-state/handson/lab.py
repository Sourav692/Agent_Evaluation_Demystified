"""Week 9 lab: replay multi-turn conversations with restarts and check state, not wording.

Usage, from new_course/:
    python3 weeks/week-09-multi-turn-state/handson/lab.py report --agent v1
    python3 weeks/week-09-multi-turn-state/handson/lab.py report --agent v1 --backend lax
    python3 weeks/week-09-multi-turn-state/handson/lab.py show conv-16 --agent v1
    python3 weeks/week-09-multi-turn-state/handson/lab.py invariance --agent v2
    python3 weeks/week-09-multi-turn-state/handson/lab.py wording
    python3 weeks/week-09-multi-turn-state/handson/lab.py freeze

Each scenario runs against a fresh in-memory refund ledger, which plays the backend that
outlives the agent, and its own checkpoint file in a temporary directory. A restart
closes the agent and builds a new one from the same checkpoint file. The checks read the
outcome and order in focus each turn reports, the tool trace and the ledger. None of
them compares the reply's wording.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.refund_store import RefundStore  # noqa: E402
from shared.session_agent import REPLIES, SESSION_AGENTS  # noqa: E402
from shared.support_agent import load_world  # noqa: E402
from shared.tool_agent import order_ids  # noqa: E402

SCENARIO_FILE = COURSE / "datasets" / "conversations" / "conversations-v1.jsonl"
GOLDEN_FILE = HERE.parent / "dataset" / "v2-transcripts.jsonl"
WORLD = load_world()
TURN_KEYS = {"customer_id", "session_id", "message", "restart_before", "expect"}
SLICES = ("restart", "clarification", "digression", "isolation", "combined")

# The same facts in different words: what a prompt edit or a model upgrade does to replies.
REWORDED_REPLIES = {
    "ask_order": "What's the order number?",
    "ask_which": "You mentioned {orders}. Which order do you mean?",
    "not_found": "Order #{n} isn't on your account. Can you double-check the number?",
    "offer": "You're eligible for a ${amount:.2f} refund on order #{n} ({item}). Want me to process it?",
    "created": "Your refund of ${amount:.2f} for order #{n} is on its way.",
    "failed": "The refund for order #{n} didn't go through ({error}). A specialist will follow up.",
    "existing": "We already refunded order #{n} ({refund_id}).",
    "final_sale": "Order #{n} was a final-sale item, which we can't refund.",
    "expired": "Order #{n} arrived {days} days ago, past our 30-day window.",
    "escalated": "I've sent order #{n} to a specialist, since refunds above $500 need one.",
    "cancelled": "Understood, order #{n} won't be refunded.",
    "answer": "Good question. {answer}",
    "no_action": "How can I help?",
}


@dataclass
class CheckResult:
    check: str
    passed: bool
    reason: str
    severity: str


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate(scenarios: list[dict]) -> None:
    """Refuse a scenario file whose turns lack a field the harness relies on."""
    for s in scenarios:
        for i, turn in enumerate(s["turns"], 1):
            missing = TURN_KEYS - turn.keys()
            if missing:
                raise ValueError(f"{s['scenario_id']} turn {i} is missing {sorted(missing)}")


# --- The harness: replay a scenario, restarting where it says --------------------------

def replay(scenario: dict, agent: str, workdir: Path, strict: bool = True,
           restarts: str = "scenario", replies: dict = REPLIES) -> dict:
    """Run every turn in order. restarts: "scenario" (as written), "none" or "every" turn."""
    ledger = RefundStore(WORLD)
    path = str(workdir / f"{scenario['scenario_id']}-{agent}-{restarts}.sqlite")
    Agent = SESSION_AGENTS[agent]
    bot, built, turns = Agent(WORLD, ledger, path, strict, replies), 1, []
    for i, turn in enumerate(scenario["turns"]):
        restart = {"scenario": turn["restart_before"], "none": False, "every": i > 0}[restarts]
        if restart:
            bot.close()
            bot, built = Agent(WORLD, ledger, path, strict, replies), built + 1
        result = bot.handle(turn["customer_id"], turn["session_id"], turn["message"])
        turns.append({"customer_id": turn["customer_id"], "session_id": turn["session_id"],
                      "message": turn["message"], "restarted": restart, "reply": result.reply,
                      "outcome": result.outcome, "order_id": result.order_id,
                      "calls": [{"name": c.name, "args": c.args, "error": c.error} for c in result.trace]})
    bot.close()
    return {"scenario_id": scenario["scenario_id"], "agent": agent, "agents_built": built, "turns": turns,
            "refunds": [{"order_id": r["order_id"], "amount": r["amount"]} for r in ledger.new_refunds()],
            "escalations": [e["order_id"] for e in ledger.events() if e["action"] == "escalated"]}


# --- Checks: state and outcomes, never wording ------------------------------------------

def check_outcomes(scenario: dict, run: dict) -> CheckResult:
    """Each turn's outcome is one the scenario accepts for that turn."""
    for i, (want, got) in enumerate(zip(scenario["turns"], run["turns"]), 1):
        if got["outcome"] not in want["expect"]["outcome"]:
            return CheckResult("outcomes", False, f"turn {i}: {got['outcome']}, expected "
                               f"{' or '.join(want['expect']['outcome'])}", "major")
    return CheckResult("outcomes", True, "every turn's outcome is acceptable", "major")


def check_order_continuity(scenario: dict, run: dict) -> CheckResult:
    """After each turn the agent is working on the order the scenario expects."""
    for i, (want, got) in enumerate(zip(scenario["turns"], run["turns"]), 1):
        if got["order_id"] != want["expect"]["order_id"]:
            return CheckResult("order_continuity", False, f"turn {i}: order in focus {got['order_id']}, "
                               f"expected {want['expect']['order_id']}", "major")
    return CheckResult("order_continuity", True, "the right order is in focus at every turn", "major")


def check_mutation_timing(scenario: dict, run: dict) -> CheckResult:
    """Refunds and escalations happen only on turns where the scenario expects them."""
    allowed = {"create_refund": "refund_created", "escalate_to_specialist": "escalated_to_human"}
    for i, (want, got) in enumerate(zip(scenario["turns"], run["turns"]), 1):
        for call in got["calls"]:
            if call["name"] in allowed and allowed[call["name"]] not in want["expect"]["outcome"]:
                return CheckResult("mutation_timing", False,
                                   f"turn {i}: {call['name']} on {call['args'].get('order_id')}", "critical")
    return CheckResult("mutation_timing", True, "mutations only where expected", "critical")


def check_ledger(scenario: dict, run: dict) -> CheckResult:
    """Read back the ledger: exactly the expected refunds and escalations, no duplicates."""
    unexpected = [r for r in run["refunds"] if r not in scenario["expected_refunds"]]
    missing = [r for r in scenario["expected_refunds"] if r not in run["refunds"]]
    extra = len(run["refunds"]) - len(scenario["expected_refunds"])
    esc = sorted(run["escalations"]) != sorted(scenario["expected_escalations"])
    if unexpected or missing or extra or esc:
        return CheckResult("ledger", False, f"unexpected {unexpected}, missing {missing}, "
                           f"escalations {run['escalations']}", "critical")
    return CheckResult("ledger", True, "ledger holds exactly the expected refunds and escalations", "critical")


def check_tenant_isolation(scenario: dict, run: dict) -> CheckResult:
    """No customer sees, or has tools called on, an order they neither own nor mentioned."""
    mentioned = defaultdict(set)
    for i, turn in enumerate(run["turns"], 1):
        me = turn["customer_id"]
        mentioned[me].update(order_ids(turn["message"]))
        touched = order_ids(turn["reply"]) + [c["args"]["order_id"] for c in turn["calls"] if "order_id" in c["args"]]
        for oid in touched:
            order = WORLD["orders"].get(oid)
            if order and order["customer_id"] != me and oid not in mentioned[me]:
                return CheckResult("tenant_isolation", False,
                                   f"turn {i}: {me} was shown or acted on {oid} of {order['customer_id']}", "critical")
    return CheckResult("tenant_isolation", True, "no foreign orders", "critical")


CHECKS = [check_outcomes, check_order_continuity, check_mutation_timing, check_ledger, check_tenant_isolation]


def evaluate(scenario: dict, run: dict) -> list[CheckResult]:
    return [check(scenario, run) for check in CHECKS]


def run_suite(agent: str, strict: bool = True, restarts: str = "scenario",
              replies: dict = REPLIES, scenarios: list[dict] | None = None) -> list[dict]:
    scenarios = scenarios if scenarios is not None else read_jsonl(SCENARIO_FILE)
    validate(scenarios)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:          # checkpoint files never touch the repo
        for s in scenarios:
            run = replay(s, agent, Path(tmp), strict, restarts, replies)
            results = evaluate(s, run)
            rows.append({"id": s["scenario_id"], "slice": s["slice"], "run": run, "results": results,
                         "passed": all(r.passed for r in results)})
    return rows


# --- Restart invariance: restarts must not change what happens --------------------------

def signature(run: dict) -> tuple:
    """What a conversation did, without its wording: outcomes, orders in focus, the ledger."""
    return (tuple((t["outcome"], t["order_id"]) for t in run["turns"]),
            tuple(sorted((r["order_id"], r["amount"]) for r in run["refunds"])),
            tuple(sorted(run["escalations"])))


def invariance(agent: str) -> list[dict]:
    """Replay each scenario with no restarts and with a restart before every turn; compare."""
    none = {r["id"]: r for r in run_suite(agent, restarts="none")}
    every = {r["id"]: r for r in run_suite(agent, restarts="every")}
    out = []
    for sid in none:
        a, b = none[sid]["run"], every[sid]["run"]
        diff = next((i for i, (x, y) in enumerate(zip(a["turns"], b["turns"]), 1)
                     if (x["outcome"], x["order_id"]) != (y["outcome"], y["order_id"])), None)
        out.append({"id": sid, "same": signature(a) == signature(b), "first_diff_turn": diff,
                    "agents_built": b["agents_built"]})
    return out


# --- Exact-text checking, for comparison --------------------------------------------------

def check_exact_text(run: dict, golden: dict) -> bool:
    """The brittle alternative: every reply identical to a recorded transcript."""
    return [t["reply"] for t in run["turns"]] == golden[run["scenario_id"]]


def load_golden() -> dict:
    return {g["scenario_id"]: g["replies"] for g in read_jsonl(GOLDEN_FILE)}


def compare_checkers(agent: str, replies: dict) -> dict:
    rows, golden = run_suite(agent, replies=replies), load_golden()
    return {"exact_text": sum(check_exact_text(r["run"], golden) for r in rows),
            "state_checks": sum(r["passed"] for r in rows), "n": len(rows)}


# --- Printing --------------------------------------------------------------------------

def print_report(agent: str, strict: bool) -> None:
    rows = run_suite(agent, strict)
    backend = "strict" if strict else "lax"
    print(f"Session agent {agent}, {backend} backend: {sum(r['passed'] for r in rows)}/{len(rows)} scenarios pass")
    print(f"{'slice':<15}{'pass':>6}")
    for name in SLICES:
        group = [r for r in rows if r["slice"] == name]
        print(f"{name:<15}{sum(r['passed'] for r in group):>3}/{len(group)}")
    failures = defaultdict(int)
    for r in rows:
        for c in r["results"]:
            failures[c.check] += not c.passed
    print("Failed checks: " + ", ".join(f"{k} {v}" for k, v in failures.items()))
    for r in rows:
        if not r["passed"]:
            first = next(c for c in r["results"] if not c.passed)
            print(f"  {r['id']} ({r['slice']}): {first.check}: {first.reason}")
    planned = sum(t["restarted"] for r in rows for t in r["run"]["turns"])
    print(f"Restarts replayed: {planned}")


def print_transcript(scenario_id: str, agent: str, strict: bool) -> None:
    scenario = next(s for s in read_jsonl(SCENARIO_FILE) if s["scenario_id"] == scenario_id)
    row = run_suite(agent, strict, scenarios=[scenario])[0]
    print(f"{scenario_id} ({scenario['slice']}): {scenario['description']}. Agent {agent}.")
    for i, t in enumerate(row["run"]["turns"], 1):
        if t["restarted"]:
            print("  --- agent restarts ---")
        print(f"  {i}. {t['customer_id']}/{t['session_id']}: {t['message']}")
        print(f"     agent: {t['reply']}")
        calls = ", ".join(f"{c['name']}({c['args'].get('order_id', '')}){'!' + c['error'] if c['error'] else ''}"
                          for c in t["calls"] if c["name"] != "search_policy")
        print(f"     outcome {t['outcome']}, order in focus {t['order_id']}, calls [{calls}]")
    print(f"  ledger: refunds {row['run']['refunds']}, escalations {row['run']['escalations']}")
    for c in row["results"]:
        print(f"  {'PASS' if c.passed else 'FAIL'} {c.check}: {c.reason}")


def print_invariance(agent: str) -> None:
    rows = invariance(agent)
    same = [r for r in rows if r["same"]]
    print(f"Session agent {agent}: {len(same)}/{len(rows)} scenarios behave the same with no restarts "
          f"and with a restart before every turn")
    for r in rows:
        if not r["same"]:
            print(f"  {r['id']}: first differs at turn {r['first_diff_turn']}")


def print_wording() -> None:
    print(f"{'agent and wording':<26}{'exact text':>12}{'state checks':>14}")
    for agent, label, replies in (("v2", "v2, recorded wording", REPLIES), ("v2", "v2, reworded", REWORDED_REPLIES),
                                  ("v1", "v1, recorded wording", REPLIES)):
        c = compare_checkers(agent, replies)
        print(f"{label:<26}{c['exact_text']:>8}/{c['n']}{c['state_checks']:>10}/{c['n']}")


def freeze() -> None:
    """Record v2's replies as the golden transcripts the exact-text check compares against."""
    rows = run_suite("v2")
    GOLDEN_FILE.write_text("".join(json.dumps({"scenario_id": r["id"], "agent": "v2",
                                               "replies": [t["reply"] for t in r["run"]["turns"]]}) + "\n"
                                   for r in rows))
    print(f"wrote {GOLDEN_FILE.relative_to(COURSE)}: {len(rows)} transcripts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("report", "show", "invariance"):
        p = sub.add_parser(name)
        if name == "show":
            p.add_argument("scenario")
        p.add_argument("--agent", default="v1", choices=list(SESSION_AGENTS))
        if name != "invariance":
            p.add_argument("--backend", default="strict", choices=["strict", "lax"])
    sub.add_parser("wording")
    sub.add_parser("freeze")
    args = parser.parse_args()
    if args.command == "wording":
        print_wording()
    elif args.command == "freeze":
        freeze()
    elif args.command == "invariance":
        print_invariance(args.agent)
    elif args.command == "show":
        print_transcript(args.scenario, args.agent, args.backend == "strict")
    else:
        print_report(args.agent, args.backend == "strict")


if __name__ == "__main__":
    main()
