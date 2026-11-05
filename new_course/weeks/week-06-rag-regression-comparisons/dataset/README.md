# Week 6 dataset

This week has no data of its own. It compares versions on the two shared case sets:

| File | What it is |
|---|---|
| `datasets/retrieval/policy-queries-v1.jsonl` | Week 4's 50 policy queries with graded section labels, scored with Week 4's metrics at k = 3 |
| `datasets/answers/answer-cases-v1.jsonl` | Week 5's 24 answer cases, scored with Week 5's seven checks. Here each version retrieves its own evidence, so the `retrieved` field is not used |
| `datasets/policies/`, `datasets/corpus/` | The help-centre corpus |

The versions themselves are in `shared/rag_pipeline.py`. Their cost and latency figures are simulated from illustrative constants in that file, not measured.

All data is synthetic. No real customers, orders or payments.
