# docs

Prose. Nothing here executes.

| Folder | What it is |
|---|---|
| [`concepts/`](concepts/) | Theory companions to both courses — definitions, gotchas, quick-reference tables. Written for random access, not sequential reading. |
| [`interactive-labs/`](interactive-labs/) | Six standalone HTML labs you can open in a browser and manipulate. Built from course 01's notebooks; the written companions are Part 6 of the field guide. Start at [`README.md`](interactive-labs/README.md). |
| [`interview-prep/`](interview-prep/) | Evaluation questions for agentic system-design rounds and 19 decomposition case studies — plus a [self-quiz drill](interview-prep/evaluation-round-drill.html), standalone HTML. |
| [`guide-audits/`](guide-audits/) | This repo measured against external evaluation guides — two audits and the teaching companion to one of them. Start at [`README.md`](guide-audits/README.md). |
| [`study-guide/`](study-guide/) | The staged [study pl The same guide in plain language, 3–4 lines per concept, each with the
  notebook that teaches it and a TODO that asks you to produce something. 21 TODOs; the file
  is its own progress tracker.

## concepts/

- [`rag-agent-tool-evaluation.md`](concepts/rag-agent-tool-evaluation.md) — the field
  guide to course 01: the taxonomy, a what-breaks-where triage table, every check as
  what-it-catches / what-it-misses / when-to-reach-for-it, LLM-as-judge failure modes, what
  each check looks like on a live system, a debugging loop, a one-page cheat sheet, and
  **Part 6**, the worked narrative behind each of the six interactive labs. Tool-agnostic —
  no framework APIs, no code, nothing to run.
- [`databricks-mlflow-evals.md`](concepts/databricks-mlflow-evals.md) — the companion to
  course 02, in four parts: the agent under test, concepts by theme, 32 gotchas as
  symptom → cause → fix, and the numbers and decision rules in one sitting.
- [`online_vs_offline_evaluation.md`](concepts/online_vs_offline_evaluation.md) — the two
  regimes side by side: what offline catches that online cannot and the reverse, what flows
  between them, and the sampling-resolution argument — why a 5% sample cannot see a
  two-point regression, and when the answer is to move the comparison offline rather than
  sample harder. §5.1 is the same argument in plain English.
