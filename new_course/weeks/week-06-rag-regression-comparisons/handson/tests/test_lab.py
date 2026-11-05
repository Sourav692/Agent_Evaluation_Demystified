"""Week 6 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-06-rag-regression-comparisons
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week06_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week06_lab"] = lab
_spec.loader.exec_module(lab)

V1, V2, V21 = lab.summarize("v1"), lab.summarize("v2"), lab.summarize("v2.1")


def test_both_versions_run_on_the_same_cases():
    assert [r["id"] for r in V1["answers"]] == [r["id"] for r in V2["answers"]]
    assert [r["id"] for r in V1["retrieval"]] == [r["id"] for r in V2["retrieval"]]


def test_candidate_improves_the_average_and_removes_critical_failures():
    assert (V1["answers_passed"], V2["answers_passed"]) == (11, 18)
    assert (V1["critical"], V2["critical"]) == (5, 0)
    assert V2["recall@3"] > V1["recall@3"] and V2["violations"] == 0


def test_average_hides_a_regression_on_the_normal_slice():
    normal = next(d for d in lab.slice_deltas(V1, V2) if d["kind"] == "answers" and d["slice"] == "normal")
    assert (normal["base"], normal["cand"]) == (7, 6)
    assert lab.paired(V1["answers"], V2["answers"], "passed")["regressed"] == ["a-002", "a-023"]


def test_release_policy_blocks_v2_and_ships_v2_1():
    verdict, reasons = lab.decide(V1, V2)
    assert verdict == "BLOCK" and reasons == ["answer slice 'normal' drops from 7 to 6 of 8"]
    assert lab.decide(V1, V21) == ("SHIP", [])


def test_gold_context_swap_separates_retrieval_from_generation():
    v1 = {r["id"]: r["cause"] for r in lab.attribute("v1")}
    assert v1["a-010"] == "retrieval" and v1["a-017"] == "generation"
    assert {r["cause"] for r in lab.attribute("v2")} == {"generation"}  # the 3.0 threshold abstains even on gold evidence


def test_ablation_shows_retrieval_metrics_and_answers_can_disagree():
    rows = {r["label"]: r for r in lab.ablate("v2.1")}
    assert rows["without rerank"]["ndcg@3"] > rows["as configured"]["ndcg@3"]
    assert rows["without rerank"]["answers_passed"] < rows["as configured"]["answers_passed"]
    assert rows["without filtered"]["critical"] == 0  # writer v2's own filter is the second layer


def test_percentile_uses_nearest_rank():
    assert lab.percentile([10, 20, 30, 40], 50) == 20 and lab.percentile([10, 20, 30, 40], 95) == 40


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-06-rag-regression-comparisons-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-06-rag-regression-comparisons-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 16


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "Release decision for v2.1 against v1: SHIP" in printed
    assert "a-021 (restricted): inconclusive" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
