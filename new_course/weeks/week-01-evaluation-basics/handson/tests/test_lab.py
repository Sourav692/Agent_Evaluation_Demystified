"""Week 1 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-01-evaluation-basics
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week01_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week01_lab"] = lab  # dataclasses look their module up here
_spec.loader.exec_module(lab)

ROWS = {case["case_id"]: (case, run, results) for case, run, results in lab.run_all(lab.load_cases())}


def failed_checks(case_id):
    return {r.check for r in ROWS[case_id][2] if not r.passed}


def test_fixture_has_30_unique_cases():
    assert len(ROWS) == 30


def test_correct_refund_passes_every_check():
    assert failed_checks("case-0001") == set()


def test_known_wrong_outcome_is_detected():
    # Change-of-mind return inside the window: v1 wrongly denies it.
    assert "exact_outcome" in failed_checks("case-0011")


def test_keyword_check_passes_a_wrong_answer():
    # "we can only refund items..." contains "refund", so the keyword check is fooled.
    assert failed_checks("case-0011") == {"exact_outcome"}


def test_forbidden_refund_on_another_customers_order_is_detected():
    assert failed_checks("case-0024") == {"exact_outcome", "required_keywords", "forbidden_actions"}


def test_forbidden_action_is_critical():
    result = next(r for r in ROWS["case-0024"][2] if r.check == "forbidden_actions")
    assert (result.category, result.severity) == ("unsafe_action", "critical")


def test_right_outcome_wrong_reason_fails_only_on_content():
    # Expired order denied, but for the wrong reason: the reply never mentions 30 days.
    assert failed_checks("case-0016") == {"required_keywords"}


def test_confusion_matrix_and_metrics_match_hand_calculation():
    labels = [c["expected_outcome"] == "refund_created" for c, _r, _x in ROWS.values()]
    predicted = [r.outcome == "refund_created" for _c, r, _x in ROWS.values()]
    cm = lab.confusion_matrix(labels, predicted)
    assert cm == {"tp": 10, "fp": 6, "fn": 2, "tn": 12}
    p, r, f1 = lab.precision_recall_f1(cm)
    assert (round(p, 3), round(r, 3), round(f1, 3)) == (0.625, 0.833, 0.714)


def test_metrics_handle_empty_denominators():
    assert lab.precision_recall_f1({"tp": 0, "fp": 0, "fn": 0, "tn": 5}) == (0.0, 0.0, 0.0)


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402  (lab.py put new_course/ on sys.path)

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-01-evaluation-basics-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-01-evaluation-basics-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 10


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert 'precision=0.625 recall=0.833 F1=0.714' in printed
    assert "label names unknown tools ['issue_refund']" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
