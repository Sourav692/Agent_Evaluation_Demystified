"""Week 15 lab: measure how sure an evaluation result is before acting on it.

Usage, from new_course/:
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py repeat
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare --runs 20
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py agreement
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py segments
    python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py report --out OUT_DIR

Two sources of variation are SIMULATED here, and the lab says which one every number comes from:
- the stochastic experiment (dataset/stochastic-experiment-v1.json): agent versions v1 and v2 pass
  each of the 100 refund cases with a probability set per slice, drawn from a seeded random number;
- Week 11's simulated judge: tool agent v2's real, deterministic outputs graded by a seeded noisy score.
The reviewer labels come from Week 3's example sheet and this week's second sheet. Both are
authored by the course, not human review. No model is called anywhere in this lab.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist, mean, pstdev

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

DATA = HERE.parent / "dataset"
EXPERIMENT = DATA / "stochastic-experiment-v1.json"
SECOND_REVIEWER = DATA / "second-reviewer-sheet-v1.csv"


def load_week_lab(folder: str, name: str):
    """Load an earlier week's lab by path, unchanged (Week 6's pattern)."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W3 = load_week_lab("week-03-judges-and-human-calibration", "week03_lab_for_w15")
W11 = load_week_lab("week-11-evaluation-harness-and-ci", "week11_lab_for_w15")


# --- The stochastic experiment (SIMULATED) ------------------------------------------------------------

def load_experiment(path: Path = EXPERIMENT) -> dict:
    exp = json.loads(path.read_text())
    probs = exp["pass_probability"]
    if set(probs["v1"]) != set(probs["v2"]):
        raise ValueError("v1 and v2 must give a pass probability for the same slices")
    if not all(0 < p < 1 for version in probs.values() for p in version.values()):
        raise ValueError("pass probabilities must be strictly between 0 and 1")
    if not 0 <= exp["case_share"] <= 1:
        raise ValueError("case_share must be between 0 and 1")
    return exp


def read_cases(exp: dict) -> list[dict]:
    cases = [json.loads(line) for name in exp["cases"]
             for line in (COURSE / name).read_text().splitlines() if line.strip()]
    missing = {c["slice"] for c in cases} - set(exp["pass_probability"]["v1"])
    if missing:
        raise ValueError(f"no pass probability for slices {sorted(missing)}")
    return [{"case_id": c["case_id"], "slice": c["slice"]} for c in cases]


def simulate_run(cases: list[dict], exp: dict, version: str, run: int) -> dict[str, int]:
    """One SIMULATED run: 1 if the case passed, 0 if it failed.

    A case passes when its score falls below a cut-off set by its slice's pass probability.
    The score mixes two standard normal draws: one fixed per case (shared by every run and
    both versions, so a hard case stays hard) and one fresh per version and run (luck).
    `case_share` sets the mix. Each draw is seeded from its own key, so results never depend
    on the order cases run in, and rerunning reproduces them exactly.
    """
    p, share = exp["pass_probability"][version], exp["case_share"]
    results = {}
    for c in cases:
        case_draw = random.Random(f"{exp['seed']}:case:{c['case_id']}").gauss(0, 1)
        run_draw = random.Random(f"{exp['seed']}:{version}:{run}:{c['case_id']}").gauss(0, 1)
        score = math.sqrt(share) * case_draw + math.sqrt(1 - share) * run_draw
        results[c["case_id"]] = int(score < NormalDist().inv_cdf(p[c["slice"]]))
    return results


def expected_pass_rate(cases: list[dict], exp: dict, version: str) -> float:
    """The rate the simulation builds in: known here, never known for a real agent."""
    p = exp["pass_probability"][version]
    return mean(p[c["slice"]] for c in cases)


# --- Intervals -----------------------------------------------------------------------------------------

def z_value(level: float) -> float:
    """1.96 for 95%: the number of standard errors on each side of the estimate."""
    return NormalDist().inv_cdf(0.5 + level / 2)


def wilson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for k passes in n cases. Stays inside 0..1 and is never zero-width."""
    if n == 0:
        return 0.0, 1.0
    z, p = z_value(level), k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def percentile_interval(values: list[float], level: float = 0.95) -> tuple[float, float]:
    """The middle `level` of the values: for 95%, the values 2.5% and 97.5% of the way up the sorted list."""
    ordered, tail = sorted(values), (1 - level) / 2
    last = len(ordered) - 1
    return ordered[round(tail * last)], ordered[round((1 - tail) * last)]


def bootstrap(ids: list[str], stat, reps: int, seed: int) -> list[float]:
    """Resample the case IDs with replacement `reps` times and compute `stat` on each resample."""
    rng = random.Random(seed)
    return [stat(rng.choices(ids, k=len(ids))) for _ in range(reps)]


# --- Comparing two versions ------------------------------------------------------------------------------

def paired_difference(a: dict[str, float], b: dict[str, float], reps: int, seed: int,
                      level: float = 0.95) -> dict:
    """B minus A on the same cases. Resample case IDs and carry both versions' results with each."""
    if set(a) != set(b):
        raise ValueError(f"not paired: {len(set(a) ^ set(b))} case IDs are in one version only")
    ids = sorted(a)
    diff = {i: b[i] - a[i] for i in ids}

    def mean_diff(sample: list[str]) -> float:
        # Rounded so that float error (1e-18 instead of 0) cannot move an interval end across zero.
        return round(sum(diff[i] for i in sample) / len(sample), 12)

    lo, hi = percentile_interval(bootstrap(ids, mean_diff, reps, seed), level)
    return {"n": len(ids), "a": mean(a.values()), "b": mean(b.values()), "diff": mean_diff(ids), "lo": lo, "hi": hi}


def unpaired_difference(a: dict[str, float], b: dict[str, float], reps: int, seed: int,
                        level: float = 0.95) -> dict:
    """The same difference with the pairing thrown away: each version's cases resampled separately."""
    rng, ids_a, ids_b = random.Random(seed), sorted(a), sorted(b)
    dist = [round(mean(b[i] for i in rng.choices(ids_b, k=len(ids_b)))
                  - mean(a[i] for i in rng.choices(ids_a, k=len(ids_a))), 12) for _ in range(reps)]
    lo, hi = percentile_interval(dist, level)
    return {"n": len(ids_a), "diff": round(mean(b.values()) - mean(a.values()), 12), "lo": lo, "hi": hi}


def discordant(a: dict[str, int], b: dict[str, int]) -> tuple[int, int]:
    """(cases only B passed, cases only A passed). Cases both pass or both fail say nothing about the change."""
    return sum(b[i] > a[i] for i in a), sum(a[i] > b[i] for i in a)


def mcnemar_exact(b_only: int, a_only: int) -> float:
    """Two-sided exact McNemar test: if the versions were equal, each discordant case is a coin flip."""
    n = b_only + a_only
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(max(b_only, a_only), n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def verdict(lo: float, hi: float) -> str:
    if lo > 0:
        return "IMPROVED"
    if hi < 0:
        return "REGRESSED"
    return "INCONCLUSIVE"


def cases_needed_paired(effect: float, discordance: float, level: float = 0.95, power: float = 0.80) -> int:
    """Cases for a paired comparison to detect `effect` with the given power.

    Each case contributes +1, 0 or -1. The variance of that per-case difference is the
    discordant share minus effect squared.
    """
    z = z_value(level) + NormalDist().inv_cdf(power)
    return math.ceil(z * z * (discordance - effect ** 2) / effect ** 2)


def cases_needed_unpaired(p_a: float, p_b: float, level: float = 0.95, power: float = 0.80) -> int:
    """Cases per version for two independent samples to detect p_b - p_a."""
    z = z_value(level) + NormalDist().inv_cdf(power)
    return math.ceil(z * z * (p_a * (1 - p_a) + p_b * (1 - p_b)) / (p_b - p_a) ** 2)


def per_case_mean(runs: list[dict[str, int]]) -> dict[str, float]:
    """Average each case over repeated runs. The case stays the unit that gets resampled."""
    return {i: mean(run[i] for run in runs) for i in runs[0]}


def compare(exp: dict, runs: int = 1, first_run: int | None = None) -> dict:
    """Compare v1 and v2 on the same 100 cases, from one run or the average of several."""
    cases, boot = read_cases(exp), exp["bootstrap"]
    start = exp["release_run"] if first_run is None else first_run
    a_runs = [simulate_run(cases, exp, "v1", r) for r in range(start, start + runs)]
    b_runs = [simulate_run(cases, exp, "v2", r) for r in range(start, start + runs)]
    a, b = per_case_mean(a_runs), per_case_mean(b_runs)
    paired = paired_difference(a, b, boot["reps"], boot["seed"], boot["level"])
    result = {"runs": runs, "first_run": start, "paired": paired, "verdict": verdict(paired["lo"], paired["hi"]),
              "unpaired": unpaired_difference(a, b, boot["reps"], boot["seed"], boot["level"]),
              "true_diff": expected_pass_rate(cases, exp, "v2") - expected_pass_rate(cases, exp, "v1")}
    if runs == 1:
        b_only, a_only = discordant(a_runs[0], b_runs[0])
        n = len(cases)
        result.update(b_only=b_only, a_only=a_only, mcnemar_p=mcnemar_exact(b_only, a_only),
                      wilson_a=wilson(sum(a_runs[0].values()), n, boot["level"]),
                      wilson_b=wilson(sum(b_runs[0].values()), n, boot["level"]),
                      cases_needed_paired=cases_needed_paired(0.02, (b_only + a_only) / n, boot["level"], exp["power"]),
                      cases_needed_unpaired=cases_needed_unpaired(paired["a"], paired["a"] + 0.02, boot["level"], exp["power"]))
    return result


# --- Repeated runs: how much one number moves with nothing changed --------------------------------------------

def repeated_runs(exp: dict) -> dict:
    """Pass counts of every SIMULATED run, the gaps between runs of the same version (an A/A test),
    and how many cases disagree between v1 and v2 in each run pair."""
    cases = read_cases(exp)
    runs = {v: [simulate_run(cases, exp, v, r) for r in range(exp["runs"])] for v in ("v1", "v2")}
    counts = {v: [sum(run.values()) for run in rs] for v, rs in runs.items()}
    diffs = [b - a for a, b in zip(counts["v1"], counts["v2"])]
    disc = [sum(discordant(a, b)) for a, b in zip(runs["v1"], runs["v2"])]
    return {"n": len(cases), "counts": counts, "diffs": diffs, "discordant": disc,
            "cases_needed_at_mean": cases_needed_paired(0.02, mean(disc) / len(cases), exp["bootstrap"]["level"], exp["power"]),
            "aa_gap": {v: max(c) - min(c) for v, c in counts.items()},
            "expected": {v: expected_pass_rate(cases, exp, v) for v in ("v1", "v2")}}


def judge_repeats(seeds: range) -> dict:
    """Week 11's tool agent v2 graded by its SIMULATED judge once per seed. The agent's output never changes."""
    passes = []
    for seed in seeds:
        run = W11.run_suite("tools", "v2", True, judge="simulated", seed=seed, now=lambda: "fixed")
        passes.append(run["summary"]["status"]["pass"])
    return {"n": len(W11.read_cases("tools")), "passes": passes, "spread": max(passes) - min(passes)}


# --- Judge and reviewer agreement ------------------------------------------------------------------------------

def load_verdicts() -> dict[str, dict[str, str]]:
    """pass/fail verdicts from the judge (Week 3's mock responses, invalid ones dropped) and two authored reviewers."""
    samples = W3.read_jsonl(W3.SAMPLES)
    judged = W3.build_report(samples, W3.read_jsonl(W3.MOCK_RESPONSES), {}, W3.policy_text())["judgments"]
    return {"judge": {i: j["verdict"] for i, j in judged.items()},
            "reviewer A": {i: r["human_verdict"] for i, r in W3.load_labels(W3.EXAMPLE_LABELS).items()},
            "reviewer B": {i: r["human_verdict"] for i, r in W3.load_labels(SECOND_REVIEWER).items()}}


def kappa_interval(x: dict[str, str], y: dict[str, str], reps: int, seed: int, level: float = 0.95) -> dict:
    """Cohen's kappa (Week 3's formula) on the cases both raters labelled, with a bootstrap interval."""
    ids = sorted(x.keys() & y.keys())

    def kappa(sample: list[str]) -> float:
        return W3.agreement([(x[i], y[i]) for i in sample])["kappa"]

    lo, hi = percentile_interval(bootstrap(ids, kappa, reps, seed), level)
    return {"n": len(ids), "agree": sum(x[i] == y[i] for i in ids), "kappa": kappa(ids), "lo": lo, "hi": hi,
            "disagree": [i for i in ids if x[i] != y[i]]}


def agreement_report(exp: dict) -> dict:
    boot, verdicts = exp["bootstrap"], load_verdicts()
    pairs = [("reviewer A", "reviewer B"), ("judge", "reviewer A"), ("judge", "reviewer B")]
    rows = {f"{x} vs {y}": kappa_interval(verdicts[x], verdicts[y], boot["reps"], boot["seed"], boot["level"])
            for x, y in pairs}
    samples = {s["case_id"]: s for s in W3.read_jsonl(W3.SAMPLES)}
    split = rows["reviewer A vs reviewer B"]["disagree"]
    return {"rows": rows,
            "settled_by_ledger": [i for i in split if W3.forbidden_call(samples[i])],
            "for_rubric_owner": [i for i in split if not W3.forbidden_call(samples[i])]}


# --- Segments ----------------------------------------------------------------------------------------------------

def slice_table(cases: list[dict], a: dict[str, int], b: dict[str, int], level: float = 0.95) -> list[dict]:
    by_slice = defaultdict(list)
    for c in cases:
        by_slice[c["slice"]].append(c["case_id"])
    rows = []
    for name, ids in sorted(by_slice.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        ka, kb = sum(a[i] for i in ids), sum(b[i] for i in ids)
        rows.append({"slice": name, "n": len(ids), "a": ka, "b": kb,
                     "wilson_a": wilson(ka, len(ids), level), "wilson_b": wilson(kb, len(ids), level)})
    return rows


def production_mixes(exp: dict) -> dict[str, dict[str, float]]:
    """Week 13's SIMULATED topic mixes, renamed to this week's slices."""
    mix = exp["production_mix"]
    traffic = json.loads((COURSE / mix["source"]).read_text())
    return {name: {mix["topic_to_slice"][t]: w for t, w in topics.items()}
            for name, topics in traffic["topic_mix"].items()}


def reweight(rates: dict[str, float], mix: dict[str, float]) -> float:
    """The overall pass rate traffic with this slice mix would see, if each slice kept its own rate."""
    return sum(w * rates[s] for s, w in mix.items()) / sum(mix.values())


def segment_report(exp: dict) -> dict:
    cases = read_cases(exp)
    a = simulate_run(cases, exp, "v1", exp["release_run"])
    b = simulate_run(cases, exp, "v2", exp["release_run"])
    runs = [simulate_run(cases, exp, "v1", r) for r in range(exp["runs"])]
    by_slice = defaultdict(list)
    for c in cases:
        by_slice[c["slice"]].append(c["case_id"])
    rates = {s: mean(run[i] for run in runs for i in ids) for s, ids in by_slice.items()}
    mixes = production_mixes(exp)
    covered = set(next(iter(mixes.values())))
    eval_mix = {s: len(by_slice[s]) for s in covered}
    return {"slices": slice_table(cases, a, b, exp["bootstrap"]["level"]), "rates_v1": rates,
            "overall": {"eval set": reweight(rates, eval_mix),
                        **{f"{name} traffic": reweight(rates, m) for name, m in mixes.items()}},
            "mixes": {"eval set": {s: n / sum(eval_mix.values()) for s, n in eval_mix.items()}, **mixes}}


# --- The reliability report ----------------------------------------------------------------------------------------

def build_report(exp: dict) -> dict:
    return {"report_version": "reliability-v1", "experiment_version": exp["experiment_version"],
            "label": exp["label"], "seed": exp["seed"], "bootstrap": exp["bootstrap"],
            "release_run": compare(exp), "twenty_runs": compare(exp, runs=exp["runs"], first_run=0),
            "repeated_runs": repeated_runs(exp), "judge_repeats": judge_repeats(range(20)),
            "agreement": agreement_report(exp), "segments": segment_report(exp)}


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def pts(x: float) -> str:
    return f"{100 * x:+.1f}"


DECISION_TEXT = {
    "IMPROVED": "The whole interval is above zero: v2 is better on cases like these.",
    "REGRESSED": "The whole interval is below zero: v2 is worse on cases like these.",
    "INCONCLUSIVE": "The interval includes zero, so the data cannot tell v2 from v1. Do not report an improvement.",
}


def report_markdown(r: dict) -> str:
    one, many, rep, jr, ag, seg = (r["release_run"], r["twenty_runs"], r["repeated_runs"],
                                   r["judge_repeats"], r["agreement"], r["segments"])
    p, q = one["paired"], many["paired"]
    lines = [
        "# Reliability report: refund agent v2 against v1", "",
        f"> {r['label']}", "",
        f"Experiment `{r['experiment_version']}`, seed {r['seed']}, bootstrap {r['bootstrap']['reps']} resamples "
        f"(seed {r['bootstrap']['seed']}), {int(100 * r['bootstrap']['level'])}% intervals.", "",
        "## Decision", "",
        f"**{one['verdict']}** on the release run: v2 {pts(p['diff'])} points, interval {pts(p['lo'])} to {pts(p['hi'])}. "
        + DECISION_TEXT[one["verdict"]]
        + f" Detecting a 2-point gain with 80% power needs about {one['cases_needed_paired']:,} paired cases at this "
        f"run's discordance and {rep['cases_needed_at_mean']:,} at the 20-run average; this run has {p['n']}.", "",
        "## Release run (one run each, the same 100 cases)", "",
        "| Version | Passed | Pass rate | Wilson interval |", "|---|---:|---:|---|",
        f"| v1 | {round(p['a'] * p['n'])} | {pct(p['a'])} | {pct(one['wilson_a'][0])} to {pct(one['wilson_a'][1])} |",
        f"| v2 | {round(p['b'] * p['n'])} | {pct(p['b'])} | {pct(one['wilson_b'][0])} to {pct(one['wilson_b'][1])} |", "",
        "| Comparison | v2 minus v1 | Interval |", "|---|---:|---|",
        f"| Paired bootstrap | {pts(p['diff'])} | {pts(p['lo'])} to {pts(p['hi'])} |",
        f"| Unpaired bootstrap (pairing discarded, for contrast) | {pts(one['unpaired']['diff'])} | "
        f"{pts(one['unpaired']['lo'])} to {pts(one['unpaired']['hi'])} |", "",
        f"Discordant cases: {one['b_only']} only v2 passed, {one['a_only']} only v1 passed. "
        f"Exact McNemar p = {one['mcnemar_p']:.2f}.", "",
        "## Twenty runs each, averaged per case", "",
        f"v2 {pts(q['diff'])} points, paired interval {pts(q['lo'])} to {pts(q['hi'])}: **{many['verdict']}**. "
        f"Repeats shrink run-to-run noise. They do not add cases, so they say nothing new about requests unlike these 100.", "",
        "## Run-to-run spread with nothing changed", "",
        f"- SIMULATED agent: v1 passed {min(rep['counts']['v1'])} to {max(rep['counts']['v1'])} of {rep['n']} over "
        f"{len(rep['counts']['v1'])} runs; v2 passed {min(rep['counts']['v2'])} to {max(rep['counts']['v2'])}. "
        f"Single-run gaps (v2 minus v1) ranged from {min(rep['diffs']):+d} to {max(rep['diffs']):+d} cases, "
        f"and {min(rep['discordant'])} to {max(rep['discordant'])} cases were discordant per run pair.",
        f"- SIMULATED judge (Week 11, tool agent v2 unchanged): {min(jr['passes'])} to {max(jr['passes'])} of {jr['n']} "
        f"cases passed over {len(jr['passes'])} seeds, a spread of {jr['spread']} cases "
        f"({100 * jr['spread'] / jr['n']:.1f} points).", "",
        "## Judge and reviewer agreement", "",
        "**Labels are authored examples, not human review.** These numbers test the method, not the judge.", "",
        "| Raters | Cases | Agree | Cohen's kappa | Interval |", "|---|---:|---:|---:|---|",
        *[f"| {name} | {row['n']} | {row['agree']} | {row['kappa']:.3f} | {row['lo']:.3f} to {row['hi']:.3f} |"
          for name, row in ag["rows"].items()], "",
        f"Reviewer disagreements settled by the ledger (a forbidden tool call): {', '.join(ag['settled_by_ledger'])}. "
        f"Sent to the rubric owner: {', '.join(ag['for_rubric_owner'])}.", "",
        "## Segments (release run)", "",
        "| Slice | Cases | v1 | v2 | v1 interval | v2 interval |", "|---|---:|---:|---:|---|---|",
        *[f"| {s['slice']} | {s['n']} | {s['a']} | {s['b']} | {pct(s['wilson_a'][0])} to {pct(s['wilson_a'][1])} | "
          f"{pct(s['wilson_b'][0])} to {pct(s['wilson_b'][1])} |" for s in seg["slices"]], "",
        "Overall v1 pass rate on seven slices, each slice at its 20-run rate, under three mixes:", "",
        *[f"- {name}: {pct(rate)}" for name, rate in seg["overall"].items()], "",
        "## Caveats", "",
        "- Every pass and fail above is SIMULATED. The spread shows what sampling noise of this size does; "
        "it is not a measurement of any model's variation.",
        "- The 100 cases are the course's golden set. An interval covers requests like these cases, not traffic the set does not represent.",
        "- Intervals assume cases are independent. Near-duplicate cases make them too narrow.",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "reliability-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "reliability-report.md").write_text(report_markdown(report))


# --- Printing ------------------------------------------------------------------------------------------------------

def print_repeat(rep: dict, jr: dict) -> None:
    print(f"SIMULATED agent, {rep['n']} cases, {len(rep['counts']['v1'])} runs per version")
    for v in ("v1", "v2"):
        c = rep["counts"][v]
        print(f"  {v}: passed {' '.join(map(str, c))}")
        print(f"      mean {mean(c):.2f}, sd {pstdev(c):.2f}, range {min(c)}-{max(c)} "
              f"(built-in rate {pct(rep['expected'][v])})")
    print(f"  v2 minus v1, run by run: {' '.join(f'{d:+d}' for d in rep['diffs'])}")
    print(f"  runs where v2 looked worse: {sum(d < 0 for d in rep['diffs'])}, "
          f"no better: {sum(d <= 0 for d in rep['diffs'])}, of {len(rep['diffs'])}")
    print(f"  discordant cases per run pair: {min(rep['discordant'])}-{max(rep['discordant'])}, "
          f"mean {mean(rep['discordant']):.1f}; paired cases for +2 points at the mean: {rep['cases_needed_at_mean']:,}")
    print(f"\nSIMULATED judge on Week 11's tool agent v2 ({jr['n']} cases, agent output identical every time)")
    print(f"  passed per seed 0-{len(jr['passes']) - 1}: {' '.join(map(str, jr['passes']))}")
    print(f"  spread {jr['spread']} cases = {100 * jr['spread'] / jr['n']:.1f} points with nothing changed")


def print_compare(c: dict) -> None:
    p, u = c["paired"], c["unpaired"]
    label = f"run {c['first_run']}" if c["runs"] == 1 else f"runs {c['first_run']}-{c['first_run'] + c['runs'] - 1}, averaged per case"
    print(f"SIMULATED v1 vs v2 on the same {p['n']} cases, {label}")
    if c["runs"] == 1:
        print(f"  v1 {pct(p['a'])}  Wilson {pct(c['wilson_a'][0])} to {pct(c['wilson_a'][1])}")
        print(f"  v2 {pct(p['b'])}  Wilson {pct(c['wilson_b'][0])} to {pct(c['wilson_b'][1])}")
        print(f"  discordant: {c['b_only']} only v2 passed, {c['a_only']} only v1 passed; "
              f"exact McNemar p = {c['mcnemar_p']:.3f}")
    else:
        print(f"  v1 {pct(p['a'])}  v2 {pct(p['b'])}")
    print(f"  paired bootstrap   v2 minus v1 {pts(p['diff'])} points, 95% interval {pts(p['lo'])} to {pts(p['hi'])}")
    print(f"  unpaired bootstrap v2 minus v1 {pts(u['diff'])} points, 95% interval {pts(u['lo'])} to {pts(u['hi'])}")
    print(f"  verdict: {c['verdict']}  (built-in difference {pts(c['true_diff'])} points)")
    if c["runs"] == 1:
        print(f"  cases needed to detect +2 points with 80% power: paired {c['cases_needed_paired']:,}, "
              f"unpaired {c['cases_needed_unpaired']:,} per version")


def print_agreement(ag: dict) -> None:
    print("AUTHORED labels (example-not-human-review): these numbers test the method, not the judge")
    print(f"{'raters':<26}{'cases':>6}{'agree':>7}{'kappa':>8}   95% interval")
    for name, row in ag["rows"].items():
        print(f"{name:<26}{row['n']:>6}{row['agree']:>7}{row['kappa']:>8.3f}   {row['lo']:.3f} to {row['hi']:.3f}")
    print(f"reviewers disagree on: {', '.join(ag['rows']['reviewer A vs reviewer B']['disagree'])}")
    print(f"  settled by the ledger (forbidden tool call): {', '.join(ag['settled_by_ledger'])}")
    print(f"  for the rubric owner: {', '.join(ag['for_rubric_owner'])}")


def print_segments(seg: dict) -> None:
    print("SIMULATED release run, by slice")
    print(f"{'slice':<26}{'cases':>6}{'v1':>4}{'v2':>4}   v1 interval        v2 interval")
    for s in seg["slices"]:
        print(f"{s['slice']:<26}{s['n']:>6}{s['a']:>4}{s['b']:>4}   "
              f"{pct(s['wilson_a'][0]):>6} to {pct(s['wilson_a'][1]):<7} {pct(s['wilson_b'][0]):>6} to {pct(s['wilson_b'][1])}")
    print("\nv1 overall on seven slices, each slice at its 20-run rate:")
    for name, rate in seg["overall"].items():
        print(f"  {name:<26}{pct(rate)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("repeat", help="run-to-run spread of the SIMULATED agent and judge")
    cmp_ = sub.add_parser("compare", help="v1 against v2: intervals, paired and unpaired bootstrap")
    cmp_.add_argument("--runs", type=int, default=1)
    cmp_.add_argument("--first-run", type=int, default=None)
    sub.add_parser("agreement", help="kappa with intervals for the judge and two authored reviewers")
    sub.add_parser("segments", help="slice intervals and the effect of the traffic mix")
    rep = sub.add_parser("report", help="write reliability-report.md and .json")
    rep.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    exp = load_experiment()
    if args.command == "repeat":
        print_repeat(repeated_runs(exp), judge_repeats(range(20)))
    elif args.command == "compare":
        if args.runs < 1:
            parser.error("--runs must be at least 1")
        print_compare(compare(exp, args.runs, args.first_run))
    elif args.command == "agreement":
        print_agreement(agreement_report(exp))
    elif args.command == "segments":
        print_segments(segment_report(exp))
    else:
        report = build_report(exp)
        write_report(report, args.out)
        print(report_markdown(report))
        print(f"wrote {args.out / 'reliability-report.md'} and reliability-report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
