# Concepts

Theory companions. These do not repeat the notebooks' explanations — they do what a
sequential notebook can't: random access.

| Document | Companion to | Use it for |
|---|---|---|
| [`rag-agent-tool-evaluation.md`](rag-agent-tool-evaluation.md) | [course 01](../../courses/01-rag-agent-tool-evaluation/) | The taxonomy of evaluation surfaces, every check as catches / misses / when-to-use, LLM-as-judge failure modes, what each looks like on a live system, a debugging loop and a cheat sheet. Tool-agnostic — the notebooks carry the framework specifics |
| [`online_vs_offline_evaluation.md`](online_vs_offline_evaluation.md) | [course 02](../../courses/02-databricks-mlflow-evals/), phases 5–7 | The one distinction the rest of the track hangs off: what each regime can see, what flows between them, and §5's sampling-resolution argument — why a 5% sample cannot see a two-point regression, with a plain-English walk-through in §5.1 |
| [`databricks-mlflow-evals.md`](databricks-mlflow-evals.md) | [course 02](../../courses/02-databricks-mlflow-evals/) | Four parts: **1** what TelcoAssist is (tools, data, models, trace shape, deliberate non-goals) · **2** every concept in a line or two, grouped by theme, pointing at the phase that demonstrates it · **3** 32 traps as symptom → cause → fix, led by the silent failures that look like success · **4** the numbers, thresholds and decision rules |
