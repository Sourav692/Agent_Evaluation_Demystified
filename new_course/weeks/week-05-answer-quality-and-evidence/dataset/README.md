# Week 5 dataset

This week has no data of its own. Its cases are shared with Week 6, so they live at the course root:

| File | What it is |
|---|---|
| `datasets/answers/answer-cases-v1.jsonl` | 24 answer cases in five slices: `normal` (8), `outdated`, `contradictory`, `missing` and `restricted` (4 each) |
| `datasets/build_answer_cases.py` | How every case was made. `normal` evidence is Week 4's filtered hybrid top 3, computed by the script. The other slices' evidence is written by hand to reproduce one problem each |
| `datasets/policies/`, `datasets/corpus/` | The help-centre corpus from Week 4, including the superseded policy and the internal playbook |

Each case has these fields:

| Field | Meaning |
|---|---|
| `case_id` | Stable ID, `a-001` to `a-024` |
| `question` | The customer's question |
| `slice` | The evidence problem the case reproduces |
| `retrieved` | The chunk IDs the writer receives, in order |
| `expected_behavior` | `answer` or `abstain` |
| `must_include` | Facts a correct answer must state (answer cases only) |
| `must_not_include` | Facts a correct answer must never state, applied to every case |
| `gold_sections` | Sections that answer the question |
| `reference_answer` | A correct answer, also used as the Ragas reference |
| `label_source` | `author-labeled, one annotator`: written by the course author and not reviewed by a second person |

All data is synthetic. No real customers, orders or payments.
