# Interview prep

Evaluation questions of the kind asked when you are designing or decomposing an agentic
system — judgement under a constraint, not coding exercises or metric derivations.

## Start here

| File | What it is |
|---|---|
| [`evaluation-study-plan.html`](evaluation-study-plan.html) | **The reading path.** Seven stages ordered by what the round actually tests, with time estimates, a 2–3 day fast path, an explicit skip list, and a readiness check. Open it in a browser; tick items off as you go. |
| [`evaluation-round-drill.html`](evaluation-round-drill.html) | **The self-quiz.** The same 35 questions and 19 cases with every answer hidden until you reveal it. Rate your recall per item, then filter to what's still weak. Progress saves locally. |

Both are standalone — no build step, no server. Open the file.

## Source documents

- [`Evaluation_Questions_for_Agentic_System_Design.md`](Evaluation_Questions_for_Agentic_System_Design.md)
  — 35 questions across 9 parts. Each gives the issue underneath the question, what they're
  checking, a strong answer, a weak answer *with why it reads badly*, and the follow-up to expect.
- [`Agentic_AI_Evaluation_Decomposition_Case_Studies.md`](Agentic_AI_Evaluation_Decomposition_Case_Studies.md)
  (also as [HTML](Agentic_AI_Evaluation_Decomposition_Case_Studies.html)) — 19 case studies in 8
  tiers, plus the Decomposition Spine, the silent-failure catalogue, and the misreadings that
  sound like insight.

The two HTML files above are built from these; the Markdown is the canonical text.

## The shape of an answer

1. Clarify the business outcome and whose judgement defines "good".
2. Name what must never happen, separately from what should usually happen.
3. Decompose the system and say what is measurable at each layer.
4. Say where ground truth comes from, and admit what it costs.
5. Split the checks: deterministic vs judged, offline vs online.
6. Define the release decision — thresholds **and** no-regression.
7. State the gaps you're not covering, and the compensating control.

Grounded in [`../../courses/02-databricks-mlflow-evals/`](../../courses/02-databricks-mlflow-evals/)
and [`../../labs/`](../../labs/).
