"""Week 15 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-15-reliable-measurement-and-statistics
"""

import csv
import importlib.util
import json
import math
import random
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week15_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week15_lab"] = lab
_spec.loader.exec_module(lab)

EXP = lab.load_experiment()
CASES = lab.read_cases(EXP)


def release_run():
    return (lab.simulate_run(CASES, EXP, "v1", EXP["release_run"]),
            lab.simulate_run(CASES, EXP, "v2", EXP["release_run"]))


def test_simulation_is_seeded_labelled_and_independent_of_case_order():
    assert EXP["label"].startswith("SIMULATED") and len(CASES) == 100
    a, b = release_run()
    assert (sum(a.values()), sum(b.values())) == (81, 83)
    shuffled = CASES[:]
    random.Random(1).shuffle(shuffled)
    assert lab.simulate_run(shuffled, EXP, "v1", 0) == a                 # keyed by case, not position
    assert lab.simulate_run(CASES, EXP, "v1", 1) != a                    # a new run is new luck
    assert round(lab.expected_pass_rate(CASES, EXP, "v1"), 4) == 0.8114
    assert round(lab.expected_pass_rate(CASES, EXP, "v2"), 4) == 0.8314


def test_experiment_file_is_validated(tmp_path):
    bad = json.loads(lab.EXPERIMENT.read_text())
    bad["pass_probability"]["v2"]["final_sale"] = 1.0
    (tmp_path / "bad.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="strictly between 0 and 1"):
        lab.load_experiment(tmp_path / "bad.json")


def test_wilson_interval_matches_the_hand_calculation():
    lo, hi = lab.wilson(81, 100)
    assert (round(lo, 3), round(hi, 3)) == (0.722, 0.875)
    lo, hi = lab.wilson(30, 30)
    assert round(lo, 3) == 0.886 and hi == 1.0                           # 30 of 30 is not proof of 100%
    assert lab.wilson(0, 0) == (0.0, 1.0)
    assert round(lab.z_value(0.95), 2) == 1.96


def test_bootstrap_is_reproducible_and_percentiles_take_the_middle():
    ids = [f"c{i}" for i in range(10)]
    first = lab.bootstrap(ids, len, 5, seed=3)
    assert first == lab.bootstrap(ids, len, 5, seed=3) == [10] * 5    # every resample keeps the sample size
    assert lab.percentile_interval(list(range(1001))) == (25, 975)


def test_the_two_point_gain_on_the_release_run_is_inconclusive():
    c = lab.compare(EXP)
    p = c["paired"]
    assert (p["a"], p["b"], p["diff"], p["lo"], p["hi"]) == (0.81, 0.83, 0.02, -0.03, 0.08)
    assert c["verdict"] == "INCONCLUSIVE" and round(c["true_diff"], 6) == 0.02
    assert (c["b_only"], c["a_only"]) == (5, 3)
    assert c["mcnemar_p"] == 2 * (56 + 28 + 8 + 1) / 256              # C(8,5) + ... + C(8,8), both tails
    assert (c["cases_needed_paired"], c["cases_needed_unpaired"]) == (1562, 5789)
    u = c["unpaired"]
    assert (u["lo"], u["hi"]) == (-0.09, 0.12)                          # pairing discarded: twice as wide


def test_paired_comparison_refuses_different_case_sets():
    a, b = release_run()
    b.pop("case-0001")
    with pytest.raises(ValueError, match="not paired"):
        lab.paired_difference(a, b, 100, 15)


def test_sample_size_formulas_match_the_hand_calculation():
    z = lab.z_value(0.95) + lab.NormalDist().inv_cdf(0.80)              # 1.96 + 0.84 = 2.80
    assert lab.cases_needed_paired(0.02, 0.08) == math.ceil(z * z * (0.08 - 0.0004) / 0.0004) == 1562
    assert lab.cases_needed_unpaired(0.81, 0.83) == 5789


def test_repeats_narrow_the_interval_but_twenty_still_touch_zero():
    twenty = lab.compare(EXP, runs=20, first_run=0)
    assert twenty["verdict"] == "INCONCLUSIVE"
    assert twenty["paired"]["lo"] == 0.0 and twenty["paired"]["hi"] == 0.042
    forty = lab.compare(EXP, runs=40, first_run=0)
    assert forty["verdict"] == "IMPROVED" and forty["paired"]["lo"] > 0


def test_nothing_changed_and_the_numbers_still_move():
    rep = lab.repeated_runs(EXP)
    assert rep["aa_gap"] == {"v1": 12, "v2": 8}
    assert sum(d < 0 for d in rep["diffs"]) == 6 and (min(rep["diffs"]), max(rep["diffs"])) == (-5, 10)
    assert (min(rep["discordant"]), max(rep["discordant"]), rep["discordant"][0]) == (8, 24, 8)   # the release run is the luckiest
    assert rep["cases_needed_at_mean"] == 3142
    jr = lab.judge_repeats(range(20))
    assert jr["n"] == 30 and jr["spread"] == 6 and (min(jr["passes"]), max(jr["passes"])) == (23, 29)


def test_agreement_intervals_and_where_the_reviewers_split():
    with lab.SECOND_REVIEWER.open(newline="") as f:
        assert {row["label_source"] for row in csv.DictReader(f)} == {"example-not-human-review"}
    ag = lab.agreement_report(EXP)
    got = {name: (row["n"], row["agree"], round(row["kappa"], 3)) for name, row in ag["rows"].items()}
    assert got == {"reviewer A vs reviewer B": (30, 24, 0.455), "judge vs reviewer A": (26, 22, 0.505),
                   "judge vs reviewer B": (26, 22, 0.62)}
    row = ag["rows"]["judge vs reviewer A"]
    assert row["lo"] < 0 < row["kappa"] < row["hi"]                    # 26 cases cannot rule out chance agreement
    assert ag["settled_by_ledger"] == ["case-0024", "case-0025", "case-0026"]
    assert ag["for_rubric_owner"] == ["case-0017", "case-0028", "case-0029"]


def test_segments_show_noise_and_the_mix_effect():
    seg = lab.segment_report(EXP)
    missing = next(s for s in seg["slices"] if s["slice"] == "missing_order")
    assert (missing["n"], missing["a"], missing["b"]) == (7, 7, 5)    # same probability in both versions: pure noise
    assert EXP["pass_probability"]["v1"]["missing_order"] == EXP["pass_probability"]["v2"]["missing_order"]
    overall = {k: round(v, 3) for k, v in seg["overall"].items()}
    assert overall == {"eval set": 0.844, "baseline traffic": 0.858, "clearance_sale traffic": 0.765}


def test_report_is_written_with_its_label_and_verdict(tmp_path):
    report = lab.build_report(EXP)
    lab.write_report(report, tmp_path)
    md = (tmp_path / "reliability-report.md").read_text()
    assert md.count("SIMULATED") >= 3 and "**INCONCLUSIVE** on the release run" in md
    assert "Labels are authored examples, not human review." in md
    saved = json.loads((tmp_path / "reliability-report.json").read_text())
    assert saved["release_run"]["verdict"] == "INCONCLUSIVE" and saved["report_version"] == "reliability-v1"
    assert lab.main(["compare"]) == 0


def test_drill_1_pairing_by_position_widens_the_interval_silently():
    a, b = release_run()
    rows_a = [{"case_id": i, "passed": a[i]} for i in sorted(a)]
    rows_b = [{"case_id": i, "passed": b[i]} for i in sorted(b)]
    random.Random(7).shuffle(rows_b)                                    # v2's rows came back in completion order
    by_position = {ra["case_id"]: rb["passed"] for ra, rb in zip(rows_a, rows_b)}
    broken = lab.paired_difference(a, by_position, 10000, 15)           # same case IDs, so no error
    assert broken["diff"] == 0.02 and (broken["lo"], broken["hi"]) == (-0.09, 0.13)
    assert lab.discordant(a, by_position) == (17, 15)
    by_case = {r["case_id"]: r["passed"] for r in rows_b}
    assert by_case == b and lab.discordant(a, by_case) == (5, 3)


def test_drill_2_a_wald_interval_claims_certainty_from_30_of_30():
    def wald(k, n, level=0.95):
        z, p = lab.z_value(level), k / n
        half = z * math.sqrt(p * (1 - p) / n)
        return max(0.0, p - half), min(1.0, p + half)
    assert wald(30, 30) == (1.0, 1.0)
    assert wald(1, 6)[0] == 0.0                                          # clipped from a negative rate
    assert round(lab.wilson(30, 30)[0], 3) == 0.886 and round(lab.wilson(1, 6)[0], 3) == 0.030


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-15-reliable-measurement-and-statistics-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-15-reliable-measurement-and-statistics-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 25


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "verdict: INCONCLUSIVE  (built-in difference +2.0 points)" in printed
    assert "position-paired interval: -9.0 to +13.0" in printed
    assert "Wald 30/30: 100.0% to 100.0%" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
