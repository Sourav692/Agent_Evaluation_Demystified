# Week 2 dataset

| File | What it is |
|---|---|
| `broken/` | A deliberately broken copy of the dataset with 13 planted errors, and its manifest. Practice input for `validate --manifest`. |
| `few_shot_prompt.md` | A prompt whose third example is a reworded holdout case (case-0074). Practice input for `leak-check`. |

This week also reads the versioned dataset this week builds, which later weeks also use, so it lives at the course root: `datasets/development/refund-cases-v1.jsonl` (73 cases), `datasets/holdout/refund-cases-v1.jsonl` (27 cases) and `datasets/manifest.json`. The 13 fields of a case are explained in the theory file, section 3.

All data is synthetic. No real customers, orders or payments.
