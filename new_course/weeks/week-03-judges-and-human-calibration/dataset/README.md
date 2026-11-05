# Week 3 dataset

| File | What it is |
|---|---|
| `samples.jsonl` | Agent v1's runs on the 30 Week 1 cases, frozen so this week's numbers never change. Rebuild with `lab.py samples`. |
| `human_review_sheet.csv` | Blank review sheet for your own labels. `label_source` is pre-filled `human`. |
| `example_review_sheet.csv` | Example labels written by the course author, marked `example-not-human-review`. **Not human review.** |
| `mock_judge_responses.jsonl` | 30 judge responses written by hand in the judge's output format, 4 of them invalid on purpose. **Not model output.** |
| `pairwise_candidates.jsonl` | For 3 cases, v1's reply (A) and a hand-written improved reply (B). |
| `mock_pairwise_responses.jsonl` | Pairwise verdicts for those 3 pairs in both orders. **Not model output.** |

This week also reads `datasets/policies/refund-policy-2026-01.md`, the judge's only reference. Rebuilding `samples.jsonl` also reads Week 1's `dataset/cases.jsonl` and runs `shared/support_agent.py`. All 30 samples come from development cases. The holdout is never touched.

All data is synthetic. No real customers, orders or payments.
