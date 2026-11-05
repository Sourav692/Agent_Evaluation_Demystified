# Week 15 hands-on: Reliable measurement and statistics

Read the [theory](../theory/week-15-reliable-measurement-and-statistics-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/development/refund-cases-v1.jsonl   # 73 golden cases: IDs and slices only
  datasets/holdout/refund-cases-v1.jsonl       # 27 golden cases: IDs and slices only
  weeks/week-03-judges-and-human-calibration/
    handson/lab.py                             # agreement(), load_labels(), the judge-response parser
    dataset/samples.jsonl, mock_judge_responses.jsonl, example_review_sheet.csv
  weeks/week-11-evaluation-harness-and-ci/
    handson/lab.py                             # run_suite() and the SIMULATED judge
  weeks/week-13-tracing-and-online-evaluation/
    dataset/traffic-config-v1.json             # the SIMULATED topic mixes
  weeks/week-15-reliable-measurement-and-statistics/
    README.md                                  # week index
    theory/week-15-reliable-measurement-and-statistics-theory.md   (and .html)
    handson/
      week-15-reliable-measurement-and-statistics-handson.md      # this file
      week-15-reliable-measurement-and-statistics-handson.ipynb   # the same lab as a notebook
      lab.py                                   # repeat, compare, agreement, segments, report
      tests/test_lab.py
      runs/week-15/                            # written by the report command, git-ignored
    dataset/
      README.md                                # the files below and the shared data this week reads
      stochastic-experiment-v1.json            # SIMULATED: pass probabilities per slice, seed, case share
      second-reviewer-sheet-v1.csv             # AUTHORED: reviewer B's verdicts on Week 3's 30 replies
```

### The notebook

`week-15-reliable-measurement-and-statistics-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library: `random` for seeded draws, `statistics.NormalDist` for z-values and the case model, and `math.comb` for McNemar's test. It loads Week 3's and Week 11's labs by path and never edits them.

Two sources of variation in this lab are SIMULATED, and every printed block says which:

| Source | What varies | What is fixed |
| --- | --- | --- |
| The stochastic experiment | Each case's pass or fail in each run, from seeded normal draws | The 100 cases, their slices, each case's difficulty, the per-slice probabilities |
| Week 11's simulated judge | The judged verdict on each reply, from a seeded score | Tool agent v2's replies, traces and ledger, which are deterministic |

Neither is a measurement of a model. Measuring a real model's variation means rerunning it, which costs money and is not part of this lab. The reviewer labels are authored too: Week 3's example sheet is reviewer A, and this week's `second-reviewer-sheet-v1.csv` is reviewer B.

### The experiment

`dataset/stochastic-experiment-v1.json` sets everything the simulation uses:

| Field | Value | Meaning |
| --- | --- | --- |
| `cases` | development and holdout refund cases | 100 case IDs with their slices |
| `pass_probability` | per version, per slice | v2 is higher on `window_boundary` (0.50 to 0.75) and `amount_boundary` (0.50 to 0.625), equal elsewhere, which makes it exactly 2.0 points better over the 100 cases |
| `case_share` | 0.7 | How much of a result belongs to the case, shared by every run and both versions |
| `seed` | 34 | Chosen so that run 0 shows the built-in 2-point gain |
| `runs`, `release_run` | 20, 0 | Repeats per version, and which run plays the release run |
| `bootstrap` | 10,000 resamples, seed 15, 95% | Every interval in the lab |
| `power` | 0.80 | For the sample-size calculation |
| `production_mix` | Week 13's traffic file and a topic-to-slice map | The mixes in `segments` |

`simulate_run` decides one run:

```python
def simulate_run(cases: list[dict], exp: dict, version: str, run: int) -> dict[str, int]:
    p, share = exp["pass_probability"][version], exp["case_share"]
    results = {}
    for c in cases:
        case_draw = random.Random(f"{exp['seed']}:case:{c['case_id']}").gauss(0, 1)
        run_draw = random.Random(f"{exp['seed']}:{version}:{run}:{c['case_id']}").gauss(0, 1)
        score = math.sqrt(share) * case_draw + math.sqrt(1 - share) * run_draw
        results[c["case_id"]] = int(score < NormalDist().inv_cdf(p[c["slice"]]))
    return results
```

The case draw depends only on the case, so a hard case is hard for both versions in every run. The run draw is new for each version and run. Mixing two standard normal draws with weights whose squares add to 1 gives another standard normal draw, so each case still passes with its slice's probability on average. Every draw has its own seed key, so the result does not depend on the order the cases run in.

### The bootstrap, before the code

The theory's [section 5](../theory/week-15-reliable-measurement-and-statistics-theory.md#5-bootstrap-resampling) explains it in full. In one paragraph: to see how much a statistic would vary across new sets of cases, draw 100 case IDs from the 100 you have, with replacement, compute the statistic, repeat 10,000 times, and keep the middle 95% of the values. The resample stands in for a fresh golden set drawn from the same traffic.

```python
def bootstrap(ids: list[str], stat, reps: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    return [stat(rng.choices(ids, k=len(ids))) for _ in range(reps)]


def percentile_interval(values: list[float], level: float = 0.95) -> tuple[float, float]:
    ordered, tail = sorted(values), (1 - level) / 2
    last = len(ordered) - 1
    return ordered[round(tail * last)], ordered[round((1 - tail) * last)]
```

For a comparison, the statistic is computed on case IDs, and each ID carries both versions' results:

```python
def paired_difference(a, b, reps, seed, level=0.95):
    if set(a) != set(b):
        raise ValueError(f"not paired: {len(set(a) ^ set(b))} case IDs are in one version only")
    ids = sorted(a)
    diff = {i: b[i] - a[i] for i in ids}

    def mean_diff(sample):
        # Rounded so that float error (1e-18 instead of 0) cannot move an interval end across zero.
        return round(sum(diff[i] for i in sample) / len(sample), 12)

    lo, hi = percentile_interval(bootstrap(ids, mean_diff, reps, seed), level)
    return {"n": len(ids), "a": mean(a.values()), "b": mean(b.values()), "diff": mean_diff(ids), "lo": lo, "hi": hi}
```

`unpaired_difference` draws each version's cases separately, for contrast. `per_case_mean` averages each case over repeated runs before the comparison. The case stays the unit that gets resampled. The rounding matters: without it, the 20-run comparison's lower end comes out as 1.9e-18 instead of 0, which turns INCONCLUSIVE into IMPROVED.

### The other functions

| Function | What it does |
| --- | --- |
| `wilson(k, n)` | Wilson interval for k passes in n cases |
| `discordant(a, b)` | (cases only B passed, cases only A passed) |
| `mcnemar_exact(b_only, a_only)` | Two-sided exact test of the discordant split as coin flips |
| `verdict(lo, hi)` | IMPROVED if the interval is above zero, REGRESSED if below, INCONCLUSIVE otherwise |
| `cases_needed_paired(effect, discordance)` | (z_α + z_β)² × (q − d²) / d² |
| `cases_needed_unpaired(p_a, p_b)` | (z_α + z_β)² × (p_a(1 − p_a) + p_b(1 − p_b)) / d², per version |
| `judge_repeats(seeds)` | Week 11's `run_suite` on tool agent v2 with the SIMULATED judge, once per seed |
| `load_verdicts()` | The judge's valid mock verdicts and reviewers A and B, through Week 3's parser and `load_labels` |
| `kappa_interval(x, y)` | Week 3's `agreement()` kappa on the shared cases, with a bootstrap interval |
| `slice_table`, `reweight` | Wilson intervals per slice, and the overall rate under another mix |
| `build_report`, `write_report` | Everything above as `reliability-report.json` and `.md` |

### Run it

All output below is from an unmodified checkout. Every number in it is SIMULATED or comes from AUTHORED labels.

**Repeated runs:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py repeat
```

```text
SIMULATED agent, 100 cases, 20 runs per version
  v1: passed 81 76 79 80 80 86 82 81 76 83 83 78 84 75 79 74 76 83 79 76
      mean 79.55, sd 3.26, range 74-86 (built-in rate 81.1%)
  v2: passed 83 84 83 85 85 82 79 81 79 80 78 77 84 83 83 84 84 79 80 79
      mean 81.60, sd 2.46, range 77-85 (built-in rate 83.1%)
  v2 minus v1, run by run: +2 +8 +4 +5 +5 -4 -3 +0 +3 -3 -5 -1 +0 +8 +4 +10 +8 -4 +1 +3
  runs where v2 looked worse: 6, no better: 8, of 20
  discordant cases per run pair: 8-24, mean 16.1; paired cases for +2 points at the mean: 3,142

SIMULATED judge on Week 11's tool agent v2 (30 cases, agent output identical every time)
  passed per seed 0-19: 29 24 29 28 24 27 25 25 25 27 29 25 29 23 25 27 26 24 27 27
  spread 6 cases = 20.0 points with nothing changed
```

**The release run:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare
```

```text
SIMULATED v1 vs v2 on the same 100 cases, run 0
  v1 81.0%  Wilson 72.2% to 87.5%
  v2 83.0%  Wilson 74.5% to 89.1%
  discordant: 5 only v2 passed, 3 only v1 passed; exact McNemar p = 0.727
  paired bootstrap   v2 minus v1 +2.0 points, 95% interval -3.0 to +8.0
  unpaired bootstrap v2 minus v1 +2.0 points, 95% interval -9.0 to +12.0
  verdict: INCONCLUSIVE  (built-in difference +2.0 points)
  cases needed to detect +2 points with 80% power: paired 1,562, unpaired 5,789 per version
```

**Twenty runs per version, averaged per case:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare --runs 20 --first-run 0
```

```text
SIMULATED v1 vs v2 on the same 100 cases, runs 0-19, averaged per case
  v1 79.5%  v2 81.6%
  paired bootstrap   v2 minus v1 +2.1 points, 95% interval +0.0 to +4.2
  unpaired bootstrap v2 minus v1 +2.1 points, 95% interval -5.9 to +9.9
  verdict: INCONCLUSIVE  (built-in difference +2.0 points)
```

The lower end is exactly 0.0: the interval still contains zero.

**Agreement:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py agreement
```

```text
AUTHORED labels (example-not-human-review): these numbers test the method, not the judge
raters                     cases  agree   kappa   95% interval
reviewer A vs reviewer B      30     24   0.455   0.070 to 0.793
judge vs reviewer A           26     22   0.505   -0.061 to 0.885
judge vs reviewer B           26     22   0.620   0.264 to 0.913
reviewers disagree on: case-0017, case-0024, case-0025, case-0026, case-0028, case-0029
  settled by the ledger (forbidden tool call): case-0024, case-0025, case-0026
  for the rubric owner: case-0017, case-0028, case-0029
```

"Settled by the ledger" uses Week 3's `forbidden_call`: the frozen v1 run for that case refunded an order the customer does not own, which the ledger records whatever any reviewer thought.

**Segments:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py segments
```

```text
SIMULATED release run, by slice
slice                      cases  v1  v2   v1 interval        v2 interval
damaged_in_window             22  22  22    85.1% to 100.0%   85.1% to 100.0%
change_of_mind_in_window      10   9  10    59.6% to 98.2%    72.2% to 100.0%
other_customers_order         10   9   9    59.6% to 98.2%    59.6% to 98.2%
high_value                     9   6   7    35.4% to 87.9%    45.3% to 93.7%
damaged_expired                8   6   6    40.9% to 92.9%    40.9% to 92.9%
expired                        7   6   7    48.7% to 97.4%    64.6% to 100.0%
final_sale                     7   4   4    25.0% to 84.2%    25.0% to 84.2%
missing_order                  7   7   5    64.6% to 100.0%   35.9% to 91.8%
window_boundary                6   2   3     9.7% to 70.0%    18.8% to 81.2%
already_refunded               5   5   5    56.6% to 100.0%   56.6% to 100.0%
prompt_injection               5   3   2    23.1% to 88.2%    11.8% to 76.9%
amount_boundary                4   2   3    15.0% to 85.0%    30.1% to 95.4%

v1 overall on seven slices, each slice at its 20-run rate:
  eval set                  84.4%
  baseline traffic          85.8%
  clearance_sale traffic    76.5%
```

The seven slices are the ones Week 13's topics map onto. "eval set" weights them by their case counts in the golden set.

**The reliability report:**

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py report --out weeks/week-15-reliable-measurement-and-statistics/handson/runs/week-15
```

It prints the Markdown report and writes it beside `reliability-report.json`. The decision section:

```text
## Decision

**INCONCLUSIVE** on the release run: v2 +2.0 points, interval -3.0 to +8.0. The interval includes zero, so the data cannot tell v2 from v1. Do not report an improvement. Detecting a 2-point gain with 80% power needs about 1,562 paired cases at this run's discordance and 3,142 at the 20-run average; this run has 100.
```

The rest has the same tables as the commands above, plus the A/A spreads and a caveats section. The JSON holds every number, including each run's pass count and each slice's 20-run rate.

| JSON key | Contents |
| --- | --- |
| `report_version`, `experiment_version`, `label`, `seed`, `bootstrap` | What produced the report |
| `release_run`, `twenty_runs` | `compare()` for 1 run and for 20 runs: paired and unpaired intervals, verdict, built-in difference; the release run adds discordant counts, McNemar's p, Wilson intervals and cases needed |
| `repeated_runs`, `judge_repeats` | Every run's pass count per version, the run-by-run gaps, and the judge's pass count per seed |
| `agreement` | Kappa, interval and disagreements for each pair of raters, split into ledger-settled and rubric-owner cases |
| `segments` | Slice counts with Wilson intervals, v1's 20-run slice rates, each mix and the overall rate under it |

Run the tests:

```bash
python3 -m pytest weeks/week-15-reliable-measurement-and-statistics
```

All 17 tests pass. They pin the seeded, order-independent simulation and its label, validation of the experiment file, the Wilson interval against the hand calculation, a reproducible bootstrap and percentile interval, the INCONCLUSIVE release run with its discordant counts, McNemar's p and cases needed, the refusal to pair different case sets, the sample-size formulas, the 20-run and 40-run comparisons, the A/A spreads, the kappa intervals and reviewer splits, the segment noise and mix effect, the written report, and both drills. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Wilson by hand.** Compute the Wilson interval for v2's 83 of 100, following the theory's [worked example](../theory/week-15-reliable-measurement-and-statistics-theory.md#121-worked-example-the-wilson-interval-for-81-of-100). Then compute the rule-of-three bound for 0 failures in 10 cases.
2. **Every run as a release run.** Run `compare --first-run N` for each run 0 to 19. How many of the 20 single runs give IMPROVED, and what gain does that run report?
3. **Repeats against cases.** Run `compare --runs N --first-run 0` for N = 5, 10, 40 and 80. Record the difference and the interval's width. Where does the width stop falling, and why does the difference head toward +1.6 rather than +2.0?
4. **The case share.** In the notebook's "Your own experiment" cell, set `case_share` to 0.0 and then 0.95. For each, record the discordant counts, the paired and unpaired intervals and the paired cases needed.
5. **Fix the rubric.** Suppose the rubric's owner rules that asking for a missing order number is a next step, so reviewer B relabels case-0028 and case-0029 as pass. Predict the change, then compute the new reviewer kappa in the notebook with `kappa_interval`.
6. **The mix by hand.** Using v1's 20-run slice rates from the report's JSON (`segments.rates_v1`), compute the change in the overall rate from baseline to clearance-sale traffic. Which slice contributes most?

### Reading an inconclusive result

Start with the interval, not the point estimate. If it contains zero, the data cannot tell the versions apart at this sample size. Then read the discordant count: it says how many cases carried any evidence. A small count means the versions behave alike on almost every case, and the comparison needs many more cases or a set concentrated where the versions differ. Check the pairing next: a discordant count far above what an A/A test shows, or a paired interval as wide as the unpaired one, points to results joined on the wrong key. Finally, decide whether the claimed effect matters. If it does, compute the cases it needs and grow the set. If it does not, ship or hold on other evidence and leave the number out of the release notes.

## 2. Two debugging drills

### Drill 1: the paired interval is as wide as the unpaired one

**Break it.** The notebook's drill cell writes each version's release-run results as a list of `{"case_id", "passed"}` rows, shuffles v2's list as parallel workers would return it, and joins the two lists by position: `{r1["case_id"]: r2["passed"] for r1, r2 in zip(rows_v1, rows_v2)}`.

**Symptom.**

```text
❌ position-paired interval: -9.0 to +13.0, discordant (17, 15)
✅ case-ID-paired interval: -3.0 to +8.0, discordant (5, 3)
```

No error is raised. Both dictionaries have the same 100 keys and `paired_difference`'s check passes. The difference is still +2.0 because the totals did not change.

**Diagnosis.**

1. Compare the paired interval with the unpaired one. Paired comparisons on correlated cases should be much narrower. Here they are the same width.
2. Count the discordant cases: 32, against 8 on the correct join and 8 to 24 across the 20 correctly joined run pairs. Most cases now compare v1 on one request with v2 on another.
3. Spot-check one case ID in both raw lists. v2's row for `case-0001` is not at the position v1's is.

**Fix and verify.** Build v2's dictionary from its own rows' case IDs, `{r["case_id"]: r["passed"] for r in rows_v2}`, as the lab does everywhere. The interval returns to −3.0 to +8.0 with 5 and 3 discordant. `test_drill_1_pairing_by_position_widens_the_interval_silently` pins both. Week 11's runner keeps results in input order (`pool.map`), which is why this bug cannot happen there, but any export that sorts or streams results can reintroduce it.

### Drill 2: a critical slice reports 100% to 100%

**Break it.** A report puts a Wald interval, the estimate plus and minus 1.96 standard errors, on every slice. The notebook's drill cell defines it as `wald_interval` and applies it to 30 of 30 and 1 of 6.

**Symptom.**

```text
❌ Wald 30/30: 100.0% to 100.0%
✅ Wilson 30/30: 88.6% to 100.0%
❌ Wald 1/6: 0.0% to 46.5%
✅ Wilson 1/6: 3.0% to 56.4%
```

**Diagnosis.**

1. A zero-width interval from 30 cases is impossible evidence: 30 cases cannot pin a rate exactly.
2. Compute the standard error: √(1 × 0 / 30) = 0. Wald's half-width is 1.96 × 0.
3. At 1 of 6 the Wald interval runs below zero before clipping, and its upper end is too low. Wald assumes a symmetric, roughly normal spread, which fails near 0, near 1 and at small n.

**Fix and verify.** Use `wilson`, which keeps a term that does not vanish at the edges. For zero failures, the rule of three gives a quick upper bound on the failure rate: 3 / 30 = 10%. `test_drill_2_a_wald_interval_claims_certainty_from_30_of_30` pins both.

## 3. Completion criteria

- [ ] `lab.py compare` prints INCONCLUSIVE for the release run with a paired interval of −3.0 to +8.0, and you can say which 8 cases carry the evidence.
- [ ] You can explain the bootstrap's five steps without code, and why it resamples case IDs rather than runs.
- [ ] You can compute the Wilson interval for 81 of 100 and the paired cases a 2-point gain needs by hand.
- [ ] You can explain why 20 repeats narrow the interval to 0.0 to +4.2 but not further, and what would.
- [ ] You can read the agreement table and say why kappa from 26 authored labels is not a calibration result.
- [ ] You can explain the 9-point drop under the clearance-sale mix without any slice changing.
- [ ] You can reproduce both drills' broken and fixed output.
- [ ] `python3 -m pytest weeks/week-15-reliable-measurement-and-statistics` reports 17 passed.

## 4. Solutions

**Exercise 1.** p = 0.83, z² = 3.8416. Centre = (0.83 + 0.019208) / 1.038416 = 0.8178. Half-width = 1.96 × √(0.83 × 0.17 / 100 + 0.000096) / 1.038416 = 1.96 × √0.001507 / 1.038416 = 0.0733. Interval 74.5% to 89.1%, as the lab prints. With 0 failures in 10 cases the rule of three gives a failure rate below 30%.

**Exercise 2.** 19 runs are INCONCLUSIVE and 1 is IMPROVED: run 15, which shows +10 points with an interval of +1 to +19. That run is right that v2 is better, and five times too optimistic about how much. A team that ran the comparison until it cleared zero, or picked the best of several runs, would report that run.

**Exercise 3.**

| Runs | Difference | Interval | Width |
| --- | --- | --- | --- |
| 1 | +2.0 | −3.0 to +8.0 | 11.0 |
| 5 | +4.8 | +0.6 to +9.2 | 8.6 |
| 10 | +1.7 | −1.0 to +4.6 | 5.6 |
| 20 | +2.1 | 0.0 to +4.2 | 4.2 |
| 40 | +1.8 | +0.3 to +3.6 | 3.3 |
| 80 | +1.4 | +0.1 to +3.1 | 3.0 |

The width stops falling near 3 points: what remains is case sampling. Five runs already clear zero, by luck, with a difference more than twice the true one. The difference heads toward +1.6 because that is v2's effect on these particular 100 cases, given their fixed difficulties. The built-in +2.0 is the effect averaged over every possible difficulty. Repeats estimate the first, and only more cases bring it closer to the second.

**Exercise 4.**

| `case_share` | v1, v2 | Discordant | Paired interval | Unpaired interval | Paired cases needed |
| --- | --- | --- | --- | --- | --- |
| 0.0 | 80, 85 | 12, 7 | −3.0 to +14.0 | −6.0 to +15.0 | 3,721 |
| 0.7 (as shipped) | 81, 83 | 5, 3 | −3.0 to +8.0 | −9.0 to +12.0 | 1,562 |
| 0.95 | 79, 82 | 4, 1 | −1.0 to +8.0 | −8.0 to +14.0 | 974 |

With no case effect, every run is independent, many cases disagree by luck, and pairing gains little. The more a result belongs to the case, the fewer discordant cases, the narrower the paired interval and the fewer cases needed. The unpaired interval does not benefit. The release run itself also changes with `case_share`, which is why the pass counts differ.

**Exercise 5.** The reviewers now disagree on 4 replies instead of 6 (case-0017 and the three ledger cases). Kappa rises from 0.455 to 0.586, interval 0.143 to 0.902. One rubric decision moved agreement more than any judge change could, and the interval stays wide because 30 labels is still few.

**Exercise 6.** The change in the overall rate is the sum, over slices, of the change in share times the slice's rate. The shares add to 1 in both mixes, so the gains and losses in share cancel, and only the rates decide the sign.

| Slice | Share change | 20-run rate | Contribution (points) |
| --- | --- | --- | --- |
| `final_sale` | +0.35 | 60.71% | +21.25 |
| `damaged_in_window` | −0.15 | 97.73% | −14.66 |
| `missing_order` | −0.06 | 68.57% | −4.11 |
| `other_customers_order` | −0.04 | 92.50% | −3.70 |
| `expired` | −0.04 | 91.43% | −3.66 |
| `already_refunded` | −0.03 | 76.00% | −2.28 |
| `high_value` | −0.03 | 72.78% | −2.18 |

The total is −9.34 points: 85.8% to 76.5%. Thirty-five points of share move into the slice with the lowest rate, out of slices that pass 69% to 98% of cases. No slice's own rate changed.

**Design review.** The model answers are in the [theory file's design review](../theory/week-15-reliable-measurement-and-statistics-theory.md#13-design-review).
