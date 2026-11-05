"""Week 5 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-05-answer-quality-and-evidence
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week05_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week05_lab"] = lab
_spec.loader.exec_module(lab)

from shared.answerer import Answer  # noqa: E402

FIXED = {r["case"]["case_id"]: r for r in lab.run_cases()}
FILTERED = {r["case"]["case_id"]: r for r in lab.run_cases(retrieval="filtered")}


def failed(rows, case_id):
    return {res.check for res in rows[case_id]["results"] if not res.passed}


def test_answer_set_has_24_cases_in_five_slices():
    cases = lab.read_jsonl(lab.CASES)
    assert len(cases) == 24
    assert {c["slice"] for c in cases} == {"normal", "outdated", "contradictory", "missing", "restricted"}


def test_normal_answers_pass_every_check():
    assert all(not failed(FIXED, cid) for cid, r in FIXED.items() if r["case"]["slice"] == "normal")


def test_outdated_answer_is_faithful_but_wrong():
    assert failed(FIXED, "a-009") == {"correctness", "stale_source"}


def test_missing_evidence_produces_an_unsupported_claim_and_no_abstention():
    assert failed(FIXED, "a-017") == {"faithfulness", "citation_support", "abstention"}


def test_internal_playbook_text_is_a_critical_failure():
    result = next(res for res in FIXED["a-021"]["results"] if res.check == "restricted_source")
    assert not result.passed and result.severity == "critical"
    assert "correctness" in failed(FIXED, "a-021")  # "$25 goodwill credit" is a forbidden fact


def test_filtered_retrieval_removes_stale_and_internal_sources():
    assert all({"stale_source", "restricted_source"}.isdisjoint(failed(FILTERED, cid)) for cid in FILTERED)


def test_filtered_retrieval_can_lose_the_gold_section():
    # The current R2 never reaches the writer: a retrieval failure, visible as a relevance failure.
    assert failed(FILTERED, "a-009") == {"correctness", "relevance"}


def test_missing_evidence_fails_with_either_retrieval():
    assert failed(FILTERED, "a-017") == failed(FIXED, "a-017")


def test_citation_check_catches_a_sentence_cited_to_the_wrong_chunk():
    row = FIXED["a-001"]
    (s1, c1), (s2, c2) = row["answer"].sentences
    swapped = Answer(row["answer"].text, [(s1, c2), (s2, c1)], writer="swapped")
    assert lab.check_faithfulness(row["case"], row["evidence"], swapped).passed
    assert not lab.check_citation_support(row["case"], row["evidence"], swapped).passed


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-05-answer-quality-and-evidence-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-05-answer-quality-and-evidence-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 15


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "Critical failures (internal text in an answer): []" in printed
    assert "After normalizing ranges" in printed
    assert "Ragas skipped" not in printed  # the paid cell is tagged skip-execution


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
