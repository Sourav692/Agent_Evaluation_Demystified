# Week 15 dataset

This week's data is one experiment definition and one review sheet. Every pass and fail the lab reports is generated from the experiment file, and every review label is authored by the course.

## Files in this folder

| File | What it is | Provenance |
|---|---|---|
| `stochastic-experiment-v1.json` | The experiment: which cases, the pass probability of v1 and v2 per slice, the case share, the seed, the number of runs, the bootstrap settings, the power, and the production mixes to reweight by | **SIMULATED.** Written by the course author. The probabilities and the case share are chosen to teach, not measured from any agent. The seed (34) was chosen so that run 0 shows the built-in 2-point gain |
| `second-reviewer-sheet-v1.csv` | Reviewer B's verdicts and scores for Week 3's 30 sampled replies, in the same columns as Week 3's sheets | **AUTHORED, not human review.** Written by the course author from Week 3's `example_review_sheet.csv`, with six verdicts changed to create the disagreements the lab studies. `label_source` is `example-not-human-review` on every row |

## The experiment's fields

| Field | Meaning |
|---|---|
| `experiment_version`, `label` | `stochastic-v1`, and the SIMULATED label the report repeats |
| `cases` | Course-root case files. Only `case_id` and `slice` are read |
| `seed`, `seed_note` | The seed for every draw, and why it was chosen |
| `case_share`, `case_share_note` | The share of a case's result that belongs to the case (shared by every run and both versions). 0.7 here |
| `runs`, `release_run` | Runs per version for the repeat analysis (20), and the run treated as the release run (0) |
| `bootstrap` | `reps` 10,000, `seed` 15, `level` 0.95 |
| `power` | 0.80, for the sample-size calculation |
| `pass_probability` | `v1` and `v2`, each a probability per slice, strictly between 0 and 1. v2 differs on `window_boundary` (0.75 against 0.50) and `amount_boundary` (0.625 against 0.50) |
| `production_mix` | The Week 13 traffic file to read topic mixes from, and the map from its topics to this week's slices. Topics with no slice are left out |

## Reviewer B's changes from reviewer A

| Case | Reviewer A | Reviewer B | B's reason |
|---|---|---|---|
| case-0017 | fail, 2 | pass, 3 | The rubric scores a correct decision with a wrong reason as 3, which is a pass |
| case-0024, 0025, 0026 | pass, 4 | fail, 1 | The order belongs to another customer, visible from other replies in the sample |
| case-0028, 0029 | pass, 5 | fail, 2 | The rubric's pass needs a next step, and asking for the order number does not say what happens after |

The other 24 rows match reviewer A, with `reviewer` set to `course-example-b`.

## Course-root files this week reads

| Path | Used for |
|---|---|
| `datasets/development/refund-cases-v1.jsonl`, `datasets/holdout/refund-cases-v1.jsonl` | The 100 golden case IDs and their slices. No order details are read, and no exercise cites a holdout case |
| `weeks/week-03-judges-and-human-calibration/handson/lab.py` | `agreement()` (Cohen's kappa), `load_labels()`, `build_report()` to parse the mock judge responses, `forbidden_call()` |
| `weeks/week-03-judges-and-human-calibration/dataset/` | `samples.jsonl`, `mock_judge_responses.jsonl` (mock, hand-written) and `example_review_sheet.csv` (reviewer A, authored) |
| `weeks/week-11-evaluation-harness-and-ci/handson/lab.py` | `run_suite()` with the SIMULATED judge, on Week 7's 30 tool cases |
| `weeks/week-13-tracing-and-online-evaluation/dataset/traffic-config-v1.json` | The SIMULATED baseline and clearance-sale topic mixes |

Generated reports go to `handson/runs/`, which is gitignored.

## What is not real evidence

- **Every pass rate is SIMULATED.** The experiment shows what sampling noise of a chosen size does to a comparison. It does not measure how much any model varies between runs.
- **The judge's spread is SIMULATED.** Week 11's judge is a seeded score, not a model.
- **Both review sheets are AUTHORED.** Kappa between them, or between either and the mock judge, tests the method. It is not a calibration result.
- **The traffic mixes are SIMULATED.** They come from Week 13's synthetic traffic.

All data is synthetic. No real customers, orders or payments.
