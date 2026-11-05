"""Week 3 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-03-judges-and-human-calibration
"""

import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week03_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week03_lab"] = lab
_spec.loader.exec_module(lab)

POLICY = lab.policy_text()
SAMPLES = lab.read_jsonl(lab.SAMPLES)
LABELS = lab.load_labels(lab.EXAMPLE_LABELS)
REPORT = lab.build_report(SAMPLES, lab.read_jsonl(lab.MOCK_RESPONSES), LABELS, POLICY)
QUOTE = "A customer can request a refund within 30 days of delivery."


def judgment(**changes):
    data = {"verdict": "pass", "score": 4, "rule_ids": ["R2"], "quotes": [QUOTE], "reasoning": "ok"}
    data.update(changes)
    return json.dumps(data)


def test_frozen_samples_match_agent_v1():
    assert SAMPLES == lab.build_samples()


def test_prompt_contains_policy_message_and_reply_but_no_label():
    sample = next(s for s in SAMPLES if s["case_id"] == "case-0024")
    prompt = lab.render_prompt(sample)
    assert "## R6." in prompt and sample["message"] in prompt and sample["final_text"] in prompt
    assert "access_denied" not in prompt and "{{" not in prompt


def test_parser_accepts_valid_and_fenced_json():
    assert lab.parse_judgment(judgment(), POLICY)[0]["verdict"] == "pass"
    assert lab.parse_judgment("```json\n" + judgment() + "\n```", POLICY)[1] is None


def test_parser_fails_closed_on_bad_responses():
    bad = {
        "not JSON": "Verdict: pass",
        "verdict": judgment(verdict="ok"),
        "score": judgment(score=7),
        "contradicts": judgment(verdict="pass", score=2),
        "no rule_ids": judgment(rule_ids=[]),
        "do not exist": judgment(rule_ids=["R9"]),
        "quote not found": judgment(quotes=["Damaged items are always refundable."]),
    }
    for expected, raw in bad.items():
        parsed, error = lab.parse_judgment(raw, POLICY)
        assert parsed is None and expected in error, (expected, error)


def test_quote_check_ignores_line_breaks_and_spacing():
    assert lab.parse_judgment(judgment(quotes=["A customer can request a refund\n within 30 days of delivery."]), POLICY)[1] is None


def test_report_counts_invalid_responses():
    assert sorted(REPORT["invalid"]) == ["case-0008", "case-0014", "case-0021", "case-0030"]


def test_agreement_and_kappa_match_hand_calculation():
    a = REPORT["agreement"]
    assert (a["n"], a["tp"], a["fp"], a["fn"], a["tn"]) == (26, 3, 2, 2, 19)
    assert (round(a["observed"], 3), round(a["kappa"], 3)) == (0.846, 0.505)


def test_kappa_is_zero_when_agreement_is_only_chance():
    a = lab.agreement([("pass", "pass"), ("pass", "fail"), ("fail", "pass"), ("fail", "fail")])
    assert a["observed"] == 0.5 and a["kappa"] == 0.0


def test_fluent_unsafe_reply_passes_judge_but_fails_safety_check():
    sample = next(s for s in SAMPLES if s["case_id"] == "case-0024")
    assert REPORT["judgments"]["case-0024"]["score"] == 5
    assert lab.forbidden_call(sample)
    assert "case-0024" in REPORT["judge_passed_forbidden"]


def test_example_labels_are_marked_as_not_human():
    assert set(REPORT["label_sources"]) == {"example-not-human-review"}


def test_blank_sheet_has_no_labels():
    assert lab.load_labels(lab.FIXTURES / "human_review_sheet.csv") == {}


def test_pairwise_keeps_only_order_independent_winners():
    result = lab.pairwise_consistency(lab.read_jsonl(lab.MOCK_PAIRWISE))
    assert result == {"pair-0011": "B", "pair-0018": "B", "pair-0028": "position-dependent"}


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402  (lab.py put new_course/ on sys.path)

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-03-judges-and-human-calibration-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-03-judges-and-human-calibration-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 12


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "Cohen's kappa=0.505" in printed
    assert 'fail-closed 4, fail-open 3' in printed
    assert 'pair-0028: position-dependent' in printed
    assert 'Live judge' not in printed  # the paid cell is tagged skip-execution


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
