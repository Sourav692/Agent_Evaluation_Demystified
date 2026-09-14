# Courses

Finished, sequential material. Each course is designed to be worked through in order —
later notebooks assume state and vocabulary established earlier.

| # | Course | Notebooks | What it teaches |
|---|---|---|---|
| 01 | [`01-rag-agent-tool-evaluation/`](01-rag-agent-tool-evaluation/) | 15 | The metric surface: deterministic retrieval → LLM-judged retrieval → generator (referenceless and reference-based) → RAG in-pipeline → RAGAS → multi-turn → tool use → task completion → trajectory → production tracing → CrewAI capstone |
| 02 | [`02-databricks-mlflow-evals/`](02-databricks-mlflow-evals/) | 11 | The operational loop: build one agent, then strategy, tracing, offline eval, custom judges, eval datasets mined from traces, prompt-regression gating, online monitoring, judge alignment, GEPA optimisation, adversarial edge cases |

**They complement rather than repeat each other.** Course 01 is about *which number to
compute and what it means*; course 02 is about *the machinery that computes it
continuously and decides whether to ship*. Course 01 module 2.4 and course 02 are both
MLflow — read 01 first if you want the metric intuition before the tooling.

Theory companions for both live in [`../docs/concepts/`](../docs/concepts/).
