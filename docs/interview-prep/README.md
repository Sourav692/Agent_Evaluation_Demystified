# Interview prep

Evaluation questions of the kind asked when you are designing or decomposing an agentic
system — judgement under a constraint, not coding exercises or metric derivations.

## Start here

| File | What it is |
|---|---|
| [`../study-guide/evaluation-study-plan.html`](../study-guide/evaluation-study-plan.html) | **The reading path.** Seven stages ordered by what the round actually tests, with time estimates, a 2–3 day fast path, an explicit skip list, and a readiness check. Open it in a browser; tick items off as you go. |
| [`stratified-reporting-explained.html`](stratified-reporting-explained.html) | **One concept, explained simply.** Why a single overall score is the most dangerous number on a dashboard — built around one table where quality improves and a language segment halves at the same time. Written for the interview, not the deep dive. |
| [`evaluation-round-drill.html`](evaluation-round-drill.html) | **The self-quiz.** The same 35 questions and 19 cases with every answer hidden until you reveal it. Rate your recall per item, then filter to what's still weak. Progress saves locally. |

Both are standalone — no build step, no server. Open the file.

## The source document

- [`QUESTION_BANK.md`](QUESTION_BANK.md) — **everything in one file.** Part 0 is the framing
  (what the round measures, the Decomposition Spine, the taxonomy). Parts 1–9 are 35 questions,
  each with the issue underneath it, what they're checking, a strong answer, a weak answer *with
  why it reads badly*, and the follow-up to expect. Tiers A–H are 19 case studies answered out
  loud in 30–45 minutes. Appendices A–E carry the silent-failure catalogue, the misreadings
  that sound like insight, company-specific flavour, a rapid-fire drill set and the closing notes.

The two HTML files above are built from `QUESTION_BANK.md`; the Markdown is the canonical text.
Edit there, not in the HTML.

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
