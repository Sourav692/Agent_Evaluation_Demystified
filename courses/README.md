# Courses

Finished, sequential material. Each course is designed to be worked through in order —
later notebooks assume state and vocabulary established earlier.

| # | Course | Track | Notebooks | What it teaches |
|---|---|---|---|---|
| 01 | [`01-rag-agent-tool-evaluation/`](01-rag-agent-tool-evaluation/) | Core | 15 | The metric surface: deterministic retrieval → LLM-judged retrieval → generator (referenceless and reference-based) → RAG in-pipeline → RAGAS → multi-turn → tool use → task completion → trajectory → production tracing → CrewAI capstone |
| 02 | [`02-databricks-mlflow-evals/`](02-databricks-mlflow-evals/) | **Optional** | 11 | The operational loop: build one agent, then strategy, tracing, offline eval, custom judges, eval datasets mined from traces, prompt-regression gating, online monitoring, judge alignment, GEPA optimisation, adversarial edge cases |
| 03 | [`03-agentic-eval-harness/`](03-agentic-eval-harness/) | Core | 12 | The decision layer: one LangGraph multi-agent system built only to be measured, a stratified golden set, RAGAS and DeepEval across three levels (tool → agent/handoff → end-to-end), safety assertions, custom judges, human calibration, statistics without pandas, and **a release gate wired to CI** |

**They complement rather than repeat each other.** Course 01 is about *which number to
compute and what it means*; course 02 is about *the machinery that computes it
continuously and decides whether to ship*; course 03 is about *the decision itself* — the
thresholds, the strata they are applied within, and the thing that refuses a deploy.

**Course 02 is optional.** The core path is course 01, then course 03. Course 02 teaches the
same loop on MLflow and Databricks. Phases 0–5 and 9–10 run locally against
`sqlite:///mlflow.db`, but phases 6–8 need a real Databricks workspace. Take it if you have a
workspace or work on Databricks. Course 03 covers its concepts (gating, online evaluation,
judge alignment, safety) without one.

Course 01 notebook 11 (`11_Same_Evals_with_MLflow.ipynb`) and course 02 are both MLflow. Read
course 01 first if you want the metric intuition before the tooling.

**Course 03 is complete.** All 12 notebooks are implemented. It also breaks one convention on
purpose: where course 02 shares mutable `.py` modules between notebooks, course 03 forbids
shared modules entirely and hands off through files in `data/`. Its README explains why.

Theory companions for both live in [`../docs/concepts/`](../docs/concepts/).
