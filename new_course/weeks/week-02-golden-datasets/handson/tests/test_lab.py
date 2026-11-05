"""Week 2 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-02-golden-datasets
"""

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parents[1]
_spec = importlib.util.spec_from_file_location("week02_lab", HERE / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week02_lab"] = lab
_spec.loader.exec_module(lab)

WORLD = lab.load_world()
POLICIES = lab.known_policy_versions()
SPLITS, ERRORS = lab.validate_dataset()
BY_ID = {c["case_id"]: c for cases in SPLITS.values() for c in cases}


def errors_for(case_id, **changes):
    record = copy.deepcopy(BY_ID[case_id])
    record.update(changes)
    return lab.validate_record(record, WORLD, POLICIES)


def test_shipped_dataset_is_valid_and_split_73_27():
    assert ERRORS == []
    assert (len(SPLITS["development"]), len(SPLITS["holdout"])) == (73, 27)


def test_week1_ids_are_stable_and_in_development():
    dev_ids = {c["case_id"] for c in SPLITS["development"]}
    assert {f"case-{i:04d}" for i in range(1, 31)} <= dev_ids


def test_every_slice_appears_in_holdout():
    assert {c["slice"] for c in SPLITS["holdout"]} == lab.SLICES


def test_rejects_unknown_outcome():
    assert any("expected_outcome" in e for e in errors_for("case-0001", expected_outcome="refund_create"))


def test_rejects_missing_and_unknown_fields():
    record = copy.deepcopy(BY_ID["case-0001"])
    del record["risk"]
    record["notes"] = "x"
    errors = lab.validate_record(record, WORLD, POLICIES)
    assert "missing fields ['risk']" in errors and "unknown fields ['notes']" in errors


def test_rejects_wrong_type():
    assert errors_for("case-0001", required_keywords="refund") == ["required_keywords has type str"]


def test_rejects_refund_label_on_another_customers_order():
    errors = errors_for("case-0024", expected_outcome="refund_created", forbidden_actions=[])
    assert any("must be access_denied" in e for e in errors)


def test_rejects_denial_that_allows_create_refund():
    assert errors_for("case-0013", forbidden_actions=[]) == [
        "a case that must not refund has to forbid create_refund"]


def test_rejects_unknown_policy_and_unknown_tool():
    assert any("no policy file" in e for e in errors_for("case-0001", policy_version="2025-07"))
    assert any("unknown tools" in e for e in errors_for("case-0013", forbidden_actions=["issue_refund"]))


def test_broken_fixture_reports_every_planted_error():
    _splits, errors = lab.validate_dataset(HERE.parent / "dataset" / "broken" / "manifest.json")
    text = "\n".join(errors)
    for expected in ["not valid JSON", "duplicate case_id case-0011",
                     "case-0024 is in both development and holdout",
                     "holdout case-0110 repeats the message of development case-0033",
                     "world owner is cust-004", "does not match"]:
        assert expected in text


def test_edited_file_breaks_the_manifest_hash(tmp_path):
    shutil.copytree(lab.DATASETS, tmp_path / "datasets", ignore=shutil.ignore_patterns("*.py"))
    dev = tmp_path / "datasets" / "development" / "refund-cases-v1.jsonl"
    dev.write_text(dev.read_text().replace('"risk": "critical"', '"risk": "high"', 1))
    _splits, errors = lab.validate_dataset(tmp_path / "datasets" / "manifest.json")
    assert any("sha256 mismatch" in e for e in errors)


def test_leak_check_finds_reworded_holdout_example():
    prompt = (HERE.parent / "dataset" / "few_shot_prompt.md").read_text()
    assert lab.check_prompt_leakage(prompt, SPLITS["holdout"]) == ["case-0074"]
    assert lab.check_prompt_leakage("Customer: hello", SPLITS["holdout"]) == []


def test_slice_report_exposes_critical_slices_behind_the_average():
    report = lab.slice_report(SPLITS["development"])
    assert report["other_customers_order"] == (8, 0, 7)
    assert sum(ok for _n, ok, _bad in report.values()) == 45


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402  (lab.py put new_course/ on sys.path)

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-02-golden-datasets-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-02-golden-datasets-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 9


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert 'Broken copy: 13 errors' in printed
    assert 'Holdout cases found after the fix: []' in printed
    assert 'sha256 mismatch' in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
