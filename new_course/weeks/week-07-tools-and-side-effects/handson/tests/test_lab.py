"""Week 7 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-07-tools-and-side-effects
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week07_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week07_lab"] = lab
_spec.loader.exec_module(lab)

ROWS = {(a, s): {r["case"]["case_id"]: r for r in lab.run_all(a, s)}
        for a in ("v1", "v2") for s in (False, True)}


def failed(agent, strict, case_id):
    return {x.check for x in ROWS[(agent, strict)][case_id]["results"] if not x.passed}


def test_tool_case_set_has_30_cases_in_eight_slices():
    cases = lab.read_jsonl(lab.CASES)
    assert len(cases) == 30 and len({c["slice"] for c in cases}) == 8


def test_reference_agent_on_strict_backend_passes_everything():
    assert all(r["passed"] for r in ROWS[("v2", True)].values())


def test_matrix_counts():
    s = {k: lab.summary(list(v.values())) for k, v in ROWS.items()}
    assert [s[k]["passed"] for k in [("v1", False), ("v1", True), ("v2", False), ("v2", True)]] == [2, 7, 25, 30]
    assert (len(s[("v1", True)]["stored_unexpected"]), len(s[("v1", True)]["false_success"])) == (3, 11)


def test_strict_backend_cannot_stop_a_refund_on_the_wrong_order():
    row = ROWS[("v1", True)]["t-008"]
    assert [r["order_id"] for r in row["runtime"].store.new_refunds()] == ["ord-217"]
    assert {"argument_values", "ledger"} <= failed("v1", True, "t-008")


def test_success_message_without_a_stored_refund_is_caught():
    row = ROWS[("v1", True)]["t-016"]
    assert row["result"].outcome == "refund_created" and row["runtime"].store.new_refunds() == []
    assert {"response_handling", "claim_matches_ledger"} <= failed("v1", True, "t-016")


def test_lax_backend_lets_v1_refund_another_customers_order():
    row = ROWS[("v1", False)]["t-011"]
    assert [r["order_id"] for r in row["runtime"].store.new_refunds()] == ["ord-134"]
    assert {"authorization", "ledger"} <= failed("v1", False, "t-011")


def test_lax_backend_leaks_data_even_to_an_agent_that_refuses():
    assert failed("v2", False, "t-011") == {"authorization"}
    assert ROWS[("v2", False)]["t-011"]["runtime"].store.new_refunds() == []


def test_missing_idempotency_key_is_a_schema_failure():
    assert "argument_schema" in failed("v1", True, "t-001")


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-07-tools-and-side-effects-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-07-tools-and-side-effects-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 16


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "Whole table: 30/30 cases fail" in printed
    assert "v1+key on strict: 13/30" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
