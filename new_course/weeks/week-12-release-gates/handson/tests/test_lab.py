"""Week 12 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-12-release-gates
"""

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week12_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week12_lab"] = lab
_spec.loader.exec_module(lab)

FIXED = lambda: "2026-11-05T12:00:00Z"  # noqa: E731
POLICY = lab.load_policy()


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    out = tmp_path_factory.mktemp("scenarios")
    rows = lab.build_scenarios(out, POLICY, now=FIXED)
    return out, {label: folder for label, folder, _what in rows}


def decide(out, candidate, policy=POLICY):
    return lab.gate(out / "v2", candidate, policy, now=FIXED)


def rules(decision, result):
    return sorted(r["id"] for r in decision["rules"] if r["result"] == result)


def test_candidates_change_only_what_they_say():
    cases = lab.W11.read_cases("tools")
    for strict in (True, False):
        base = {c["case_id"]: c["attempts"][0]["fingerprint"] for c in lab.W11.run_suite("tools", "v2", strict, now=FIXED)["cases"]}
        changed = {}
        for agent in lab.CANDIDATES:
            run = lab.W11.run_suite("tools", agent, strict, now=FIXED)
            changed[agent] = sorted(c["case_id"] for c in run["cases"] if c["attempts"][0]["fingerprint"] != base[c["case_id"]])
        assert changed["v2.1"] == []                       # only reply wording changed, and replies are not fingerprinted
        assert changed["v2.2"] == ["t-023"]                 # the one order over $1,000
        assert changed["v2.3"] == ([] if strict else ["t-015"])   # the strict backend hides the other customer's order
        assert len(changed["v2.4"]) == 19                   # one more search_policy call wherever v2 searched
    assert len(cases) == 30


def test_policy_is_validated_and_a_bad_policy_is_a_usage_error(tmp_path):
    assert POLICY["version"] == "v1" and "ILLUSTRATIVE" in POLICY["status"] and len(POLICY["sha256"]) == 64
    broken = copy.deepcopy(json.loads(lab.POLICY.read_text()))
    broken["hard_gates"][0]["min"] = 0                      # two limits on one rule
    broken["quality_gates"][0]["run"] = "canary"            # a run the policy does not define
    (tmp_path / "bad.json").write_text(json.dumps(broken))
    with pytest.raises(lab.PolicyError) as exc:
        lab.load_policy(tmp_path / "bad.json")
    assert "no-unauthorized-refunds needs exactly one limit" in str(exc.value) and "task-completion" in str(exc.value)
    with pytest.raises(SystemExit) as code:
        lab.main(["canary", "--policy", str(tmp_path / "bad.json")])
    assert code.value.code == lab.EXIT_USAGE


def test_passing_candidate_ships_and_the_report_names_its_evidence(runs, tmp_path):
    out, rows = runs
    d = decide(out, rows["passing candidate"])
    assert (d["verdict"], d["exit_code"], d["evidence_problems"]) == ("SHIP", 0, [])
    assert set(rules(d, "PASS")) == {r["id"] for g in lab.RULE_GROUPS for r in POLICY[g]}
    lab.write_decision(d, tmp_path)
    saved = json.loads((tmp_path / "decision.json").read_text())
    assert saved["candidate"]["runs"]["release"] == d["candidate"]["runs"]["release"]
    assert saved["policy"]["version"] == "v1" and "**Verdict: SHIP**" in (tmp_path / "decision.md").read_text()


def test_a_slice_regression_blocks_although_the_average_clears_the_quality_gates(runs):
    out, rows = runs
    d = decide(out, rows["slice regression"])
    assert d["verdict"] == "BLOCK" and rules(d, "FAIL") == ["no-slice-regression"]
    by_id = {r["id"]: r for r in d["rules"]}
    assert by_id["task-completion"]["result"] == "PASS"
    assert by_id["task-completion"]["values"] == [{"run": "release", "value": 0.9667}]
    assert by_id["no-slice-regression"]["cases"] == ["t-023"]
    assert d["flips"] == {"pass_to_fail": ["t-023"], "fail_to_pass": []}


def test_one_unauthorized_refund_blocks_a_candidate_with_the_baselines_pass_rate(runs):
    out, rows = runs
    d = decide(out, rows["one unauthorized refund"])
    assert d["verdict"] == "BLOCK" and rules(d, "FAIL") == ["no-unauthorized-refunds"]
    rule = next(r for r in d["rules"] if r["id"] == "no-unauthorized-refunds")
    assert rule["values"] == [{"run": "release", "value": 0}, {"run": "safety_probe", "value": 1}]
    assert rule["cases"] == ["t-015"]
    for name in ("release", "safety_probe"):
        passed = [json.loads((f / name / "results.json").read_text())["summary"]["status"]["pass"]
                  for f in (out / "v2", rows["one unauthorized refund"])]
        assert passed[0] == passed[1]                       # 30 and 30, 25 and 25: averages see nothing


def test_a_soft_gate_holds_for_a_named_owner(runs):
    out, rows = runs
    d = decide(out, rows["soft gate"])
    assert d["verdict"] == "HOLD" and rules(d, "FAIL") == ["cost-increase"]
    rule = next(r for r in d["rules"] if r["id"] == "cost-increase")
    assert rule["override"] == "release owner" and rule["values"][0]["ratio"] == 1.264


def test_every_evidence_problem_holds_and_none_ships(runs):
    out, rows = runs
    expected = {"budget-stopped run": "v2.1-budget/release: incomplete run: 6 of 30 cases",
                "tampered artifact": "v2.3-tampered/safety_probe: results.json does not match its checksum",
                "missing probe": "v2.1-no-probe/safety_probe: missing file: checksums.json",
                "other policy version": "release: baseline and candidate differ in policy_version"}
    for label, start in expected.items():
        d = decide(out, rows[label])
        assert d["verdict"] == "HOLD" and d["exit_code"] == 2
        assert d["evidence_problems"][0].startswith(start)
    tampered = decide(out, rows["tampered artifact"])
    assert "no-unauthorized-refunds" in rules(tampered, "MISSING")   # hiding the refund turned BLOCK into HOLD, never SHIP


def test_evidence_of_harm_outranks_missing_evidence(runs, tmp_path):
    out, rows = runs
    shutil.copytree(rows["one unauthorized refund"], tmp_path / "v2.3-no-release")
    shutil.rmtree(tmp_path / "v2.3-no-release" / "release")
    d = decide(out, tmp_path / "v2.3-no-release")
    assert d["verdict"] == "BLOCK" and d["evidence_problems"]      # the probe alone proves the unauthorized refund


def test_drill_1_a_gate_that_reads_a_missing_count_as_zero_ships_v2_3(runs, tmp_path, monkeypatch):
    out, rows = runs
    shutil.copytree(rows["one unauthorized refund"], tmp_path / "v2.3-old-harness")

    def old_harness(run):                                   # SIMULATED: a producer without safety counts
        del run["summary"]["safety"]
        for case in run["cases"]:
            case.pop("safety")
    lab.rewrite_artifact(tmp_path / "v2.3-old-harness" / "safety_probe", old_harness)
    assert lab.W11.verify_artifact(tmp_path / "v2.3-old-harness" / "safety_probe") == []
    fixed = decide(out, tmp_path / "v2.3-old-harness")
    assert fixed["verdict"] == "HOLD" and "no-unauthorized-refunds" in rules(fixed, "MISSING")

    def read_summary_fail_open(run, path):
        node = run["summary"]
        for key in path.split("."):
            node = node.get(key, 0) if isinstance(node, dict) else 0
        return node, []
    monkeypatch.setattr(lab, "read_summary", read_summary_fail_open)
    assert decide(out, tmp_path / "v2.3-old-harness")["verdict"] == "SHIP"


def test_drill_2_comparing_two_filtered_runs_to_each_other_ships_v2_2(tmp_path, monkeypatch):
    subset = [c for c in lab.W11.read_cases("tools") if c["slice"] != "high_value"]
    for agent in ("v2", "v2.2"):
        lab.produce(agent, tmp_path / agent, POLICY, now=FIXED, cases=subset)
    run = json.loads((tmp_path / "v2.2" / "release" / "results.json").read_text())
    assert run["complete"] and run["expected_cases"] == 27
    fixed = lab.gate(tmp_path / "v2", tmp_path / "v2.2", POLICY, now=FIXED)
    assert fixed["verdict"] == "HOLD"
    assert "missing ['t-023', 't-024', 't-025']" in fixed["evidence_problems"][0]

    def comparability_pairwise_only(base, cand, name):
        problems = [f"{name}: baseline and candidate differ in {k}" for k in
                    ("case_set", "data_sha256", "dataset_version", "policy_version")
                    if base["versions"].get(k) != cand["versions"].get(k)]
        if {c["case_id"] for c in base["cases"]} != {c["case_id"] for c in cand["cases"]}:
            problems.append(f"{name}: baseline and candidate hold different cases")
        return problems
    monkeypatch.setattr(lab, "comparability", comparability_pairwise_only)
    assert lab.gate(tmp_path / "v2", tmp_path / "v2.2", POLICY, now=FIXED)["verdict"] == "SHIP"


def test_canary_promotes_extends_and_rolls_back():
    got = {d["id"]: (d["decision"], d["exit_code"]) for d in lab.print_canary(POLICY)}
    assert got == {"v2.1-day-1": ("PROMOTE", 0), "v2.1-hour-2": ("EXTEND", 2),
                   "v2.4-day-1": ("ROLLBACK", 1), "v2.5-hour-3": ("ROLLBACK", 1)}
    stale = next(o for o in json.loads(lab.CANARY.read_text())["observations"] if o["id"] == "v2.1-hour-2")
    assert lab.canary_decision({**stale, "hours": 48}, POLICY)["decision"] == "ROLLBACK"   # out of time


def test_cli_gate_exit_codes(runs, tmp_path):
    out, rows = runs
    for label, code in (("passing candidate", 0), ("slice regression", 1), ("missing probe", 2)):
        assert lab.main(["gate", "--baseline", str(out / "v2"), "--candidate", str(rows[label])]) == code
    assert lab.main(["gate", "--baseline", str(out / "v2"), "--candidate", str(rows["one unauthorized refund"]),
                     "--out", str(tmp_path / "report")]) == 1
    assert json.loads((tmp_path / "report" / "decision.json").read_text())["verdict"] == "BLOCK"


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-12-release-gates-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-12-release-gates-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 20


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "one unauthorized refund   v2.3                BLOCK" in printed
    assert "fail-open gate: SHIP" in printed
    assert "pairwise-only check: SHIP" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
