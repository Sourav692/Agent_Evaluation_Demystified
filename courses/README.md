# Courses

Finished, sequential material. Each course is designed to be worked through in order —
later notebooks assume state and vocabulary established earlier.

| # | Course | Track | Notebooks | What it teaches |
|---|---|---|---|---|
| 01 | [`01-rag-agent-tool-evaluation/`](01-rag-agent-tool-evaluation/) | Core | 15 | The metric surface: deterministic retrieval → LLM-judged retrieval → generator (referenceless and reference-based) → RAG in-pipeline → RAGAS → multi-turn → tool use → task completion → trajectory → production tracing → CrewAI capstone |
| 02 | [`02-databricks-mlflow-evals/`](02-databricks-mlflow-evals/) | **Optional** | 11 | The operational loop: build one agent, then strategy, tracing, offline eval, custom judges, eval datasets mined from traces, prompt-regression gating, online monitoring, judge alignment, GEPA optimisation, adversarial edge cases |
| 03 | [`03-agentic-eval-harness/`](03-agentic-eval-harness/) | Core | 12 | The decision layer: one LangGraph multi-agent system built only to be measured, a stratified golden set, RAGAS and DeepEval across three levels (tool → agent/handoff → end-to-end), safety assertions, custom judges, human calibration, statistics without pandas, and **a release gate wired to CI** |
| 04 | [`04-end-to-end-eval-tutorial/`](04-end-to-end-eval-tutorial/) | Core (alternative to 03) | 14 | The same arc as course 03 on one support-desk agent, in simpler code: golden set, retrieval and generation, tool calls, trajectories, conversations, safety and red-teaming, custom judges, judge calibration, statistics and cost, a CI release gate, online evaluation. Traces and experiments in LangSmith; models set in `models.toml` |

**They complement rather than repeat each other.** Course 01 is about *which number to
compute and what it means*; course 02 is about *the machinery that computes it
continuously and decides whether to ship*; course 03 is about *the decision itself* — the
thresholds, the strata they are applied within, and the thing that refuses a deploy.

**Course 02 is optional.** The core path is course 01, then course 03 or course 04. Course 02 teaches the
same loop on MLflow and Databricks. Phases 0–5 and 9–10 run locally against
`sqlite:///mlflow.db`, but phases 6–8 need a real Databricks workspace. Take it if you have a
workspace or work on Databricks. Course 03 covers its concepts (gating, online evaluation,
judge alignment, safety) without one.

Course 01 notebook 11 (`11_Same_Evals_with_MLflow.ipynb`) and course 02 are both MLflow. Read
course 01 first if you want the metric intuition before the tooling.

**Course 03 is complete.** All 12 notebooks are implemented. It also breaks one convention on
purpose: where course 02 shares mutable `.py` modules between notebooks, course 03 forbids
shared modules entirely and hands off through files in `data/`. Its README explains why.

## Core path

The short route: course 01, then **either** course 03 (21 notebooks) **or** course 04
(23 notebooks). Both second halves take one multi-agent system from golden set to release gate
to online evaluation. Course 03 is fully run and uses a stdlib-only house style. Course 04 keeps
the code simpler, splits trajectories, conversations and red-teaming into their own notebooks,
and uses LangSmith. It covers every level of the
[roadmap](../docs/study-guide/evaluation-roadmap.md) at its minimum. The roadmap itself is the
**Full path**: the same notebooks plus every Optional one, level by level.

| # | Course | Notebook |
|---|---|---|
| 1 | 01 | [`00_Evaluation_Landscape.ipynb`](01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) |
| 2 | 01 | [`01_Retrieval_Metrics_Deterministic.ipynb`](01-rag-agent-tool-evaluation/01_Retrieval_Metrics_Deterministic.ipynb) |
| 3 | 01 | [`02_Retrieval_Metrics_LLM_Judged.ipynb`](01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb) |
| 4 | 01 | [`03_Generator_Metrics_Referenceless.ipynb`](01-rag-agent-tool-evaluation/03_Generator_Metrics_Referenceless.ipynb) |
| 5 | 01 | [`04_Generator_Metrics_Reference_Based.ipynb`](01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb) |
| 6 | 01 | [`08_MultiTurn_Conversational_Evaluation.ipynb`](01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb) |
| 7 | 01 | [`09_Tool_Use_Evaluation.ipynb`](01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb) |
| 8 | 01 | [`10_Task_Completion_Evaluation.ipynb`](01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb) |
| 9 | 01 | [`12_Agent_Trajectory_Evaluation.ipynb`](01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb) |
| 10 | 03 | [`01_knowledge_base_and_rag_agent.ipynb`](03-agentic-eval-harness/01_knowledge_base_and_rag_agent.ipynb) |
| 11 | 03 | [`02_tools_agents_and_supervisor_graph.ipynb`](03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb) |
| 12 | 03 | [`03_the_golden_set.ipynb`](03-agentic-eval-harness/03_the_golden_set.ipynb) |
| 13 | 03 | [`04_rag_evaluation_with_ragas.ipynb`](03-agentic-eval-harness/04_rag_evaluation_with_ragas.ipynb) |
| 14 | 03 | [`05_tool_call_evaluation.ipynb`](03-agentic-eval-harness/05_tool_call_evaluation.ipynb) |
| 15 | 03 | [`06_agent_handoff_and_end_to_end.ipynb`](03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb) |
| 16 | 03 | [`07_safety_and_policy_checks.ipynb`](03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) |
| 17 | 03 | [`08_building_custom_judges.ipynb`](03-agentic-eval-harness/08_building_custom_judges.ipynb) |
| 18 | 03 | [`09_human_feedback_and_calibration.ipynb`](03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb) |
| 19 | 03 | [`10_stratified_reporting_and_statistics.ipynb`](03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb) |
| 20 | 03 | [`11_the_release_gate_and_ci.ipynb`](03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) |
| 21 | 03 | [`12_online_evaluation_and_the_loop.ipynb`](03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb) |

**Or, in place of rows 10–21, course 04:**

| # | Course | Notebook |
|---|---|---|
| 10 | 04 | [`01_knowledge_base_and_rag_agent.ipynb`](04-end-to-end-eval-tutorial/01_knowledge_base_and_rag_agent.ipynb) |
| 11 | 04 | [`02_tools_agents_and_supervisor_graph.ipynb`](04-end-to-end-eval-tutorial/02_tools_agents_and_supervisor_graph.ipynb) |
| 12 | 04 | [`03_the_golden_set.ipynb`](04-end-to-end-eval-tutorial/03_the_golden_set.ipynb) |
| 13 | 04 | [`04_retrieval_evaluation.ipynb`](04-end-to-end-eval-tutorial/04_retrieval_evaluation.ipynb) |
| 14 | 04 | [`05_generation_evaluation.ipynb`](04-end-to-end-eval-tutorial/05_generation_evaluation.ipynb) |
| 15 | 04 | [`06_tool_call_evaluation.ipynb`](04-end-to-end-eval-tutorial/06_tool_call_evaluation.ipynb) |
| 16 | 04 | [`07_trajectories_and_handoffs.ipynb`](04-end-to-end-eval-tutorial/07_trajectories_and_handoffs.ipynb) |
| 17 | 04 | [`08_task_completion_and_conversations.ipynb`](04-end-to-end-eval-tutorial/08_task_completion_and_conversations.ipynb) |
| 18 | 04 | [`09_safety_and_red_teaming.ipynb`](04-end-to-end-eval-tutorial/09_safety_and_red_teaming.ipynb) |
| 19 | 04 | [`10_custom_judges.ipynb`](04-end-to-end-eval-tutorial/10_custom_judges.ipynb) |
| 20 | 04 | [`11_calibrating_judges_with_human_labels.ipynb`](04-end-to-end-eval-tutorial/11_calibrating_judges_with_human_labels.ipynb) |
| 21 | 04 | [`12_statistics_cost_and_experiments.ipynb`](04-end-to-end-eval-tutorial/12_statistics_cost_and_experiments.ipynb) |
| 22 | 04 | [`13_the_release_gate_and_ci.ipynb`](04-end-to-end-eval-tutorial/13_the_release_gate_and_ci.ipynb) |
| 23 | 04 | [`14_online_evaluation_and_the_loop.ipynb`](04-end-to-end-eval-tutorial/14_online_evaluation_and_the_loop.ipynb) |

Course 03 runs in its own environment and kernel (`agentic-eval-harness`); see its README.
Most of course 03 makes paid model calls (judges are cached after the first run).
Course 04 also has its own environment and kernel (`end-to-end-eval-tutorial`), needs
`OPENROUTER_API_KEY` and `LANGSMITH_API_KEY`, and commits its outputs so it can be read
without running; see its README.

**Optional branches**, taken after the Core notebook of the same level:

- Course 01: `05` (eval inside the pipeline), `06` (RAGAS), `07` (RAG capstone), `11` (the same
  evals in MLflow), `13` (production tracing), `14` (CrewAI capstone).
- Course 02, the whole MLflow/Databricks track. `06`–`08` need a Databricks workspace.
- The unique labs in [`../labs/`](../labs/), each named on its roadmap level.

Theory companions for both live in [`../docs/concepts/`](../docs/concepts/).
