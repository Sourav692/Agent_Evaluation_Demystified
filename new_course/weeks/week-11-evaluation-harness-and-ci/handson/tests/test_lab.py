"""Week 11 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-11-evaluation-harness-and-ci
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week11_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week11_lab"] = lab
_spec.loader.exec_module(lab)

FIXED = lambda: "2026-11-05T12:00:00Z"  # noqa: E731  (an injected clock keeps artifacts comparable)


def failed_checks(record, attempt=0):
    return [c["check"] for c in record["attempts"][attempt]["checks"] if not c["passed"]]


def test_tools_suite_reproduces_week_7_and_reads_safety_from_the_ledger():
    v1_strict = lab.run_suite("tools", "v1", True, now=FIXED)
    assert v1_strict["summary"]["status"]["pass"] == 7 and lab.exit_code(v1_strict) == lab.EXIT_FAIL
    assert v1_strict["summary"]["safety"]["false_success_claims"] == 11
    assert v1_strict["summary"]["safety"]["wrong_order_refunds"] == 3
    v1_lax = lab.run_suite("tools", "v1", False, now=FIXED)["summary"]["safety"]
    assert v1_lax == {"unauthorized_refunds": 5, "wrong_order_refunds": 4, "ineligible_refunds": 10,
                      "duplicate_refunds": 3, "false_success_claims": 0}          # Week 7's 22 bad refunds
    v2 = lab.run_suite("tools", "v2", True, now=FIXED)
    assert v2["summary"]["status"]["pass"] == 30 and lab.exit_code(v2) == lab.EXIT_PASS


def test_faults_suite_counts_duplicates_and_minor_findings_still_fail_cases():
    naive = lab.run_suite("faults", "naive_retry", False, now=FIXED)
    assert naive["summary"]["safety"]["duplicate_refunds"] == 3
    reference = lab.run_suite("faults", "stable_key", False, now=FIXED)
    assert reference["summary"]["failed_checks_by_severity"] == {"critical": 0, "major": 0, "minor": 4}
    assert lab.exit_code(reference) == lab.EXIT_FAIL       # Week 11's rule: any failed check fails the case


def test_workers_change_neither_the_results_nor_the_run_id():
    one = lab.run_suite("tools", "v1", False, workers=1, now=FIXED)
    eight = lab.run_suite("tools", "v1", False, workers=8, now=FIXED)
    assert one["cases"] == eight["cases"] and one["run_id"] == eight["run_id"]
    assert lab.run_suite("tools", "v1", False, seed=1, now=FIXED)["run_id"] != one["run_id"]
    assert lab.run_suite("tools", "v2", False, now=FIXED)["run_id"] != one["run_id"]


def test_artifact_round_trip_and_exit_codes(tmp_path):
    for agent, code in (("v2", 0), ("v1", 1)):
        lab.write_artifact(lab.run_suite("tools", agent, True, now=FIXED), tmp_path / agent)
        assert lab.verify_artifact(tmp_path / agent) == []
        assert lab.main(["verify", str(tmp_path / agent)]) == code
    run = json.loads((tmp_path / "v2" / "results.json").read_text())
    assert run["schema_version"] == "eval-run-v1" and run["started_at"] == "2026-11-05T12:00:00Z"
    assert run["versions"]["data_sha256"]["datasets/tools/tool-cases-v1.jsonl"] == lab.PINS[
        "datasets/tools/tool-cases-v1.jsonl"]
    assert run["versions"]["policy_version"] == "2026-01" and len(run["versions"]["code_sha256"]) == 64


def test_verify_rejects_tampered_missing_and_incomplete_artifacts(tmp_path):
    lab.write_artifact(lab.run_suite("tools", "v1", True, now=FIXED), tmp_path / "run")
    body = (tmp_path / "run" / "results.json").read_text()
    (tmp_path / "run" / "results.json").write_text(body.replace('"status": "fail"', '"status": "pass"', 1))
    assert lab.verify_artifact(tmp_path / "run") == ["results.json does not match its checksum"]
    assert lab.main(["verify", str(tmp_path / "run")]) == lab.EXIT_INCOMPLETE
    (tmp_path / "run" / "checksums.json").unlink()
    assert lab.verify_artifact(tmp_path / "run") == ["missing file: checksums.json"]
    assert lab.verify_artifact(tmp_path / "never-written") == ["missing file: checksums.json"]


def test_budget_stops_admission_and_the_run_is_incomplete_not_passing(tmp_path):
    run = lab.run_suite("tools", "v2", True, budget=0.02, now=FIXED)
    assert (run["completed_cases"], run["expected_cases"], run["complete"]) == (6, 30, False)
    assert run["summary"]["status"]["pass"] == 6 and run["summary"]["status"]["fail"] == 0
    assert lab.exit_code(run) == lab.EXIT_INCOMPLETE
    lab.write_artifact(run, tmp_path / "run")
    assert lab.verify_artifact(tmp_path / "run")[0].startswith("incomplete run: 6 of 30 cases")


def test_cache_hits_only_for_the_same_inputs(tmp_path):
    cache = tmp_path / "cache"
    lab.run_suite("tools", "v1", True, cache_dir=cache, now=FIXED)
    fresh = lab.run_suite("tools", "v2", True, cache_dir=cache, now=FIXED)
    assert fresh["summary"]["cache_hits"] == 0                  # another agent version never hits
    again = lab.run_suite("tools", "v2", True, cache_dir=cache, now=FIXED)
    assert again["summary"]["cache_hits"] == 30 and again["summary"]["cost_usd"] == 0.0
    strip = lambda run: [{k: v for k, v in r.items() if k not in ("cached", "cost_usd")} for r in run["cases"]]  # noqa: E731
    assert strip(again) == strip(fresh)
    assert lab.run_suite("tools", "v2", False, cache_dir=cache, now=FIXED)["summary"]["cache_hits"] == 0


def test_a_cache_key_without_the_agent_version_reports_v2_results_for_v1(tmp_path, monkeypatch):
    def cache_key_without_agent(suite, case, agent, strict, judge, seed, retries):
        parts = {"case": case, "suite": suite, "backend": "strict" if strict else "lax", "judge": judge,
                 "seed": seed, "retries": retries, "code": lab.code_sha256(suite)}
        return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()

    monkeypatch.setattr(lab, "cache_key", cache_key_without_agent)
    lab.run_suite("tools", "v2", True, cache_dir=tmp_path, now=FIXED)
    wrong = lab.run_suite("tools", "v1", True, cache_dir=tmp_path, now=FIXED)
    assert wrong["config"]["agent"] == "v1" and wrong["summary"]["status"]["pass"] == 30
    assert wrong["summary"]["safety"]["false_success_claims"] == 0      # v1 really makes 11


def test_a_retry_keeps_the_first_failure_and_the_case_is_flaky_not_pass():
    case = [c for c in lab.read_cases("tools") if c["case_id"] == "t-021"]
    once = lab.run_suite("tools", "v2", True, judge="simulated", cases=case, now=FIXED)["cases"][0]
    assert once["status"] == "fail" and failed_checks(once) == ["judge_reply_quality"]
    retried = lab.run_suite("tools", "v2", True, judge="simulated", retries=2, cases=case, now=FIXED)
    record = retried["cases"][0]
    assert record["status"] == "flaky" and len(record["attempts"]) == 2
    assert failed_checks(record, 0) == ["judge_reply_quality"] and failed_checks(record, 1) == []
    assert record["attempts"][0]["fingerprint"] == record["attempts"][1]["fingerprint"]
    assert lab.exit_code(retried) == lab.EXIT_FAIL


def test_repeats_blame_the_evaluator_not_the_agent():
    rows = lab.flake_report("tools", "v2", repeat=20)
    assert len(rows) == 12 and {r["fingerprints"] for r in rows} == {1}
    assert {r["diagnosis"] for r in rows} == {"evaluator varies: same trace and ledger, different verdict"}
    assert lab.diagnose([True, False], {"a", "b"}).startswith("agent varies")
    assert lab.diagnose([True, True], {"a"}) == "stable"


def test_usage_and_pin_errors_exit_3_before_anything_runs(tmp_path, monkeypatch):
    for argv in (["run", "--suite", "faults", "--agent", "v2", "--out", str(tmp_path)],
                 ["run", "--agent", "v2"], ["run", "--workers", "0", "--out", str(tmp_path)]):
        with pytest.raises(SystemExit) as exc:
            lab.main(argv)
        assert exc.value.code == lab.EXIT_USAGE
    assert lab.check_pins("tools") == [] and lab.check_pins("faults") == []
    monkeypatch.setitem(lab.PINS, "datasets/world.json", "0" * 64)
    assert lab.check_pins("tools")[0].startswith("datasets/world.json changed")
    with pytest.raises(SystemExit) as exc:
        lab.main(["run", "--out", str(tmp_path / "x")])
    assert exc.value.code == lab.EXIT_USAGE and not (tmp_path / "x").exists()


def test_ci_example_blocks_offline_and_keeps_paid_work_opt_in():
    workflow = (Path(__file__).parents[1] / "ci" / "week-11-eval-workflow.yml").read_text()
    offline, live = workflow.split("\njobs:\n")[1].split("  live-judge:")
    assert "lab.py run" in offline and "lab.py verify" in offline
    assert offline.count("if: always()") == 2 and "OPENAI_API_KEY" not in offline
    assert "if: github.event_name == 'workflow_dispatch' && inputs.live" in live
    assert 'if [ -z "$OPENAI_API_KEY" ]' in live and "exit 0" in live


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-11-evaluation-harness-and-ci-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-11-evaluation-harness-and-ci-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 20


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "12 unstable cases across 20 repeats" in printed
    assert "cache hits 30" in printed
    assert "forward order: 29 of 30 cases fail" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
