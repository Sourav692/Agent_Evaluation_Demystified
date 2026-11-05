"""Week 8 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-08-trajectories-and-task-completion
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week08_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week08_lab"] = lab
_spec.loader.exec_module(lab)

from shared.tools import ToolCall  # noqa: E402

CASES = lab.read_jsonl(lab.CASES)
SCORES = {name: lab.summarize(name, lab.evaluate(name)) for name in lab.AGENTS}


def test_case_set_and_reference_paths():
    assert len(CASES) == 38 and sum(c["quotes_amount"] for c in CASES) == 8
    assert SCORES["v2"]["exact"] == 38 and SCORES["v2"]["passed"] == 38


def test_match_modes():
    trace = [ToolCall("search_policy", {}), ToolCall("get_order", {}), ToolCall("create_refund", {})]
    assert not lab.match_trajectory(trace, ["get_order", "search_policy", "create_refund"], "exact")
    assert not lab.match_trajectory(trace, ["get_order", "search_policy", "create_refund"], "in_order")
    assert lab.match_trajectory(trace, ["get_order", "search_policy", "create_refund"], "any_order")
    assert lab.match_trajectory(trace, ["get_order", "create_refund"], "in_order")


def test_valid_alternative_order_passes_invariants_but_not_exact_match():
    s = SCORES["policy_first"]
    assert (s["exact"], s["passed"], s["hard_fail"], s["task_success"]) == (5, 38, 0, 38)


def test_mutation_before_ownership_is_a_hard_failure_the_outcome_misses():
    s = SCORES["refund_first"]
    assert (s["task_success"], s["hard_fail"], s["passed"]) == (38, 8, 30)
    hard = [r["id"] for r in lab.evaluate("refund_first") if r["verdict"] == "HARD FAIL"]
    assert hard == [c["case_id"] for c in CASES if c["quotes_amount"]]


def test_partial_credit_cannot_override_a_hard_failure():
    case = next(c for c in CASES if c["case_id"] == "tr-031")
    row = lab.score_case(case, *lab.run_case("refund_first", case))
    assert row["partial_credit"] == 1.0 and row["gated_score"] == 0.0 and row["verdict"] == "HARD FAIL"
    assert SCORES["refund_first"]["partial_credit"] == SCORES["v2"]["partial_credit"] == 1.0  # naive mean ties them
    assert SCORES["refund_first"]["partial_credit"] > SCORES["double_checks"]["partial_credit"]


def test_outcome_checker_reads_the_ledger_not_the_path():
    s = SCORES["drops_refund"]
    assert (s["exact"], s["task_success"], s["hard_fail"]) == (38, 29, 0)
    case = CASES[0]
    result, rt = lab.run_case("drops_refund", case)
    assert result.outcome == "refund_created" and rt.store.new_refunds() == []
    assert rt.trace[-1].error == "invalid_amount"


def test_redundancy_counts_identical_reads_but_not_post_mutation_reads():
    assert round(SCORES["double_checks"]["efficiency"], 3) == 0.760 and SCORES["double_checks"]["passed"] == 38
    read = ToolCall("get_order", {"order_id": "ord-123"})
    write = ToolCall("create_refund", {"order_id": "ord-123", "amount": 64.0})
    assert lab.redundant_calls([read, read]) == [1]
    assert lab.redundant_calls([read, write, read]) == []


def test_ownership_needs_the_signed_in_customer_on_the_lookup():
    case = next(c for c in CASES if c["case_id"] == "tr-011")
    _result, rt = lab.run_case("v1", case, strict=False)    # the lax backend returns someone else's order
    assert [c.name for c in rt.trace][0] == "get_order" and rt.trace[0].response["customer_id"] != case["customer_id"]
    assert not lab.check_trajectory(case, rt.trace)[0].passed


def test_lax_backend_shows_what_the_strict_one_blocked():
    lax = lab.summarize("refund_first", lab.evaluate("refund_first", strict=False))
    assert (lax["task_success"], lax["hard_fail"]) == (33, 8)


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-08-trajectories-and-task-completion-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-08-trajectories-and-task-completion-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 14


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "partial credit 1.00, gated score 0.00, verdict HARD FAIL" in printed
    assert "name-only check passes 9 cases the real check fails" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
