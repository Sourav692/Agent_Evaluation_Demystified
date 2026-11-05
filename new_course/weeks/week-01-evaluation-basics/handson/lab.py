"""Week 1 lab: run refund agent v1 on 30 labeled cases and check every run.

Usage, from new_course/:
    python3 weeks/week-01-evaluation-basics/handson/lab.py               # all cases + summary
    python3 weeks/week-01-evaluation-basics/handson/lab.py --case case-0001   # one trace
    python3 weeks/week-01-evaluation-basics/handson/lab.py --cases my_cases.jsonl  # your own cases

Three deterministic checks run on each case:
    exact_outcome      the agent's decision equals the labeled outcome
    required_keywords  the reply contains every required phrase
    forbidden_actions  the trace contains no forbidden tool call
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))  # new_course/, so `shared` imports

from shared.support_agent import AgentRun, load_world, run_agent  # noqa: E402

CASES_PATH = HERE.parent / "dataset" / "cases.jsonl"

# Failure taxonomy: every failed check maps to one category and a severity.
FAILURE_CATEGORY = {
    "exact_outcome": ("wrong_outcome", "major"),
    "required_keywords": ("missing_content", "minor"),
    "forbidden_actions": ("unsafe_action", "critical"),
}


@dataclass
class CheckResult:
    check: str
    passed: bool
    reason: str

    @property
    def category(self) -> str:
        return FAILURE_CATEGORY[self.check][0]

    @property
    def severity(self) -> str:
        return FAILURE_CATEGORY[self.check][1]


def load_cases(path: Path = CASES_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- The three checks -------------------------------------------------------

def check_exact_outcome(case: dict, run: AgentRun) -> CheckResult:
    passed = run.outcome == case["expected_outcome"]
    reason = (f"outcome {run.outcome}" if passed
              else f"expected {case['expected_outcome']}, got {run.outcome}")
    return CheckResult("exact_outcome", passed, reason)


def check_required_keywords(case: dict, run: AgentRun) -> CheckResult:
    text = run.final_text.lower()
    missing = [kw for kw in case["required_keywords"] if kw.lower() not in text]
    reason = "all keywords present" if not missing else f"missing {missing}"
    return CheckResult("required_keywords", not missing, reason)


def check_forbidden_actions(case: dict, run: AgentRun) -> CheckResult:
    called = [name for name in run.tool_names() if name in case["forbidden_actions"]]
    reason = "no forbidden calls" if not called else f"called forbidden {called}"
    return CheckResult("forbidden_actions", not called, reason)


CHECKS = [check_exact_outcome, check_required_keywords, check_forbidden_actions]


def evaluate(case: dict, run: AgentRun) -> list[CheckResult]:
    return [check(case, run) for check in CHECKS]


# --- Metrics ----------------------------------------------------------------

def confusion_matrix(labels: list[bool], predictions: list[bool]) -> dict[str, int]:
    """Count true/false positives/negatives for one yes/no question."""
    pairs = Counter(zip(labels, predictions))
    return {"tp": pairs[(True, True)], "fp": pairs[(False, True)],
            "fn": pairs[(True, False)], "tn": pairs[(False, False)]}


def precision_recall_f1(cm: dict[str, int]) -> tuple[float, float, float]:
    flagged = cm["tp"] + cm["fp"]
    actual = cm["tp"] + cm["fn"]
    precision = cm["tp"] / flagged if flagged else 0.0
    recall = cm["tp"] / actual if actual else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


# --- Runner -----------------------------------------------------------------

def run_all(cases: list[dict]) -> list[tuple[dict, AgentRun, list[CheckResult]]]:
    world = load_world()
    rows = []
    for case in cases:
        run = run_agent(case, world)
        rows.append((case, run, evaluate(case, run)))
    return rows


def print_report(rows) -> None:
    print(f"{'case':<10} {'result':<6} slice")
    for case, _run, results in rows:
        ok = all(r.passed for r in results)
        print(f"{case['case_id']:<10} {'PASS' if ok else 'FAIL':<6} {case['slice']}")
        for r in results:
            if not r.passed:
                print(f"{'':<17}{r.check:<18} [{r.severity}] {r.reason}")

    total = len(rows)
    passed_cases = sum(all(r.passed for r in results) for _c, _r, results in rows)
    print(f"\nCases passing every check: {passed_cases}/{total}")
    for check in CHECKS:
        name = check.__name__.removeprefix("check_")
        n = sum(r.passed for _c, _r, results in rows for r in results if r.check == name)
        print(f"  {name:<18} {n}/{total} pass")

    failures = Counter((r.category, r.severity) for _c, _r, results in rows
                       for r in results if not r.passed)
    print("\nFailures by category:")
    for (category, severity), count in sorted(failures.items()):
        print(f"  {category:<16} {severity:<9} {count}")

    fooled = [c["case_id"] for c, _r, results in rows
              if not results[0].passed and results[1].passed]
    print(f"\nKeyword check passed but outcome was wrong: {fooled}")

    labels = [c["expected_outcome"] == "refund_created" for c, _r, _res in rows]
    predicted = [r.outcome == "refund_created" for _c, r, _res in rows]
    cm = confusion_matrix(labels, predicted)
    p, rcl, f1 = precision_recall_f1(cm)
    print("\nRefund decisions (positive = refund_created):")
    print(f"  TP={cm['tp']} FP={cm['fp']} FN={cm['fn']} TN={cm['tn']}")
    print(f"  precision={p:.3f} recall={rcl:.3f} F1={f1:.3f}")


def print_trace(case: dict, run: AgentRun, results: list[CheckResult]) -> None:
    print(f"case:     {case['case_id']} ({case['slice']})")
    print(f"customer: {case['customer_id']}")
    print(f"message:  {case['message']}")
    print("tool calls:")
    for call in run.tool_calls:
        print(f"  {call.name}({json.dumps(call.args)})")
    print(f"outcome:  {run.outcome}  (expected {case['expected_outcome']})")
    print(f"reply:    {run.final_text}")
    for r in results:
        print(f"  {'PASS' if r.passed else 'FAIL'}  {r.check:<18} {r.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", help="print the full trace for one case ID")
    parser.add_argument("--cases", type=Path, default=CASES_PATH, help="JSONL file of cases")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    if args.case:
        cases = [c for c in cases if c["case_id"] == args.case]
        if not cases:
            sys.exit(f"unknown case ID: {args.case}")
        print_trace(*run_all(cases)[0])
    else:
        print_report(run_all(cases))


if __name__ == "__main__":
    main()
