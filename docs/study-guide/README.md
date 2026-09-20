# Study guide

Two files: a roadmap and a study plan. Neither needs a build step, a server or an API key.

| File | What it is |
|---|---|
| [`evaluation-roadmap.md`](evaluation-roadmap.md) | **The complete path, basic → expert.** Ten levels in four bands — orientation, RAG, agents, ground truth, judges, statistics, the gate, online, safety and multi-agent, the harness as a product — each with what to read or run, what it costs, and a *you are done when you can…* check. Then two dedicated sections: what an **OpenAI**-style round pushes on, and the **Databricks / MLflow 3** track as its own ladder. Ends with fast paths for an hour, an evening, a weekend and two weeks. |
| [`evaluation-study-plan.html`](evaluation-study-plan.html) | **The interview reading path.** Seven stages ordered by what an eval-heavy round tests, with time estimates, a 2–3 day fast path, a skip list and a readiness check. Checkboxes persist in `localStorage`, so it doubles as a tracker. |

Pick by intent: the roadmap teaches the subject; the plan prepares for the round. The rest of
this page is about the plan.

## The study plan

It holds no content of its own. It is the **reading path** through
[`../interview-prep/QUESTION_BANK.md`](../interview-prep/QUESTION_BANK.md), which is the
canonical text: seven stages ordered by what an eval-heavy interview round actually tests,
rather than by the order the material happens to sit in.

## The seven stages

| # | Stage | Time | Why here |
|---|---|---|---|
| 1 | Get the answer skeleton | 30 min | The eight-step Decomposition Spine, before any content. Highest-lever half hour in the plan. |
| 2 | The taxonomy you must be able to draw | 2–3 h | The five surfaces — retrieval, generation, tool mechanics, trajectory, outcome — plus reference-based vs referenceless. Most follow-ups are "which layer are you measuring?" in disguise. |
| 3 | The 35 questions | 6–8 h | The core. Read in the plan's order, which descends by how often each part decides the round — not front to back. |
| 4 | Rehearsal on the 19 cases | 4–6 h | Answered out loud in 30–45 min each. Apply the Spine before reading the given decomposition. |
| 5 | The four separators | 3–4 h | Where a strong answer visibly separates from a competent one. Prose-led: read the markdown, skip every code cell. |
| 6 | The numbers, last and repeatedly | 1 h, then re-skim | Specific figures are what make an answer sound operated rather than read. Re-skim the morning of. |
| 7 | Run code | 2–3 h, optional | Coding is not what this round tests. Kept to the few places execution makes an abstraction concrete. |

Roughly 17–25 hours end to end, or 15–22 without stage 7. The skip list saves about 15 more
by naming what will *not* come up.

## What it points at

- [`../interview-prep/QUESTION_BANK.md`](../interview-prep/QUESTION_BANK.md) — the source for
  stages 1, 3 and 4.
- [`../concepts/databricks-mlflow-evals.md`](../concepts/databricks-mlflow-evals.md) — stage 6:
  the p\*\*n conversation table, Wilson resolution, regression tolerances, weighted kappa.
- [`../interactive-labs/`](../interactive-labs/) — stage 7, best effort-to-insight ratio here.
- [`../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb`](../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb)
  — stage 5, the offline/online boundary.

## Related

[`../interview-prep/evaluation-round-drill.html`](../interview-prep/evaluation-round-drill.html)
is the other half: the same 35 questions and 19 cases with every answer hidden, for
self-quizzing once you have read them. Plan first, drill second.

Both pages are built from `QUESTION_BANK.md` and neither is canonical — edit the Markdown,
not the HTML.
