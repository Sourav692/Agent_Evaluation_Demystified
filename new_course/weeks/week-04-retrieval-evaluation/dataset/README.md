# Week 4 dataset

| File | What it is |
|---|---|
| `hand_rankings.jsonl` | Three fixed rankings (H1 to H3) with labels, written to be checked by hand. Fixtures, not retriever output. |

This week also reads data shared with Week 6, so it lives at the course root:

| File | What it is |
|---|---|
| `datasets/policies/refund-policy-2026-01.md` | The current refund policy, R1 to R6 (public) |
| `datasets/corpus/*.md` | Six more help-centre documents: shipping, warranty, exchanges, payments, the superseded 2025-06 refund policy and an internal escalation playbook |
| `datasets/retrieval/policy-queries-v1.jsonl` | 50 policy queries in six slices, each labeling policy sections with graded relevance (3 answers, 2 needed context, 1 related) |

Each document's front matter carries `status` (current or superseded) and `audience` (public or internal). The metadata filter in `shared/retrieval.py` keeps only current, public chunks.

Each query has these fields:

| Field | Meaning |
|---|---|
| `query_id` | Stable ID, `q-001` to `q-050` |
| `query` | The customer's question |
| `slice` | `direct`, `paraphrase`, `exact_term`, `outdated_trap`, `restricted_trap` or `multi_section` |
| `relevance` | Section ID to grade, current public sections only |
| `label_source` | `author-labeled, one annotator`: written by the course author and not reviewed by a second person |

All data is synthetic. No real customers, orders or payments.
