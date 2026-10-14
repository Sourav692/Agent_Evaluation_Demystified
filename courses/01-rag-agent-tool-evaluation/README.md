# RAG, Agent & Tool Evaluation — Tutorial

**Status:** ✅ Built — all modules (0 through 5) complete. See `archive/TUTORIAL_PLAN.md` for the full build plan, source mapping, and build-time notes.

A single, ordered learning path through everything this repo has for evaluating RAG systems, tool-calling agents, and multi-turn conversational agents — pulled together from the notebooks and scripts previously scattered across `labs/rag-evaluation/`, `labs/agent-evaluation/`, `archive/labs-multiturn-and-tool-eval/`, and `labs/langgraph-agent-rag-eval/`. Nothing was deleted from those folders; this tutorial is additive and, where a module references material with real relative-path or live-service dependencies (Module 4's Arize labs, Module 5's CrewAI app), links to it in place rather than copying it.

**Target environment:** `deepeval==4.1.8` (repo root `.venv`). If you run an original source notebook directly instead of this tutorial's version, check that notebook's own folder for a different pin first.

**📖 [`rag-agent-tool-evaluation.md`](../../docs/concepts/rag-agent-tool-evaluation.md)** — the field guide to everything below: taxonomy, reference-based vs. referenceless, LLM-as-judge failure modes, every check as what it catches / what it misses / when to reach for it, how each is computed once a system is live, plus a debugging loop and a one-page cheat sheet — no code, no API calls, no environment needed. Deliberately tool-agnostic: the notebooks show how each idea is expressed in a given framework, the guide covers the idea. Read it standalone (to study or prep for an interview) or alongside the notebooks as a lookup.

## Prerequisites

- **Python 3.12+** and the repo-root environment described in the root [`README.md`](../../README.md#setup) Setup section (this course has no environment of its own). Module 4 needs the `phoenix` extra and a running Phoenix server; Module 5's CrewAI app needs the `crewai` extra.
- **`OPENAI_API_KEY`** in a root `.env` (copy [`.env.example`](../../.env.example)). Almost every notebook calls a paid model.
- **Free to run (no API calls):** `00_Evaluation_Landscape.ipynb`, `01_Retrieval_Metrics_Deterministic.ipynb`, the mocked part of `05_RAG_Eval_Inside_the_Pipeline.ipynb`, and Parts A–B of `12_Agent_Trajectory_Evaluation.ipynb`.
- Notebook outputs are cleared in git; nothing below has been run for you.

## Table of contents

| # | Notebook | Covers | Status |
|---|---|---|---|
| 0 | [`00_Evaluation_Landscape.ipynb`](00_Evaluation_Landscape.ipynb) | Taxonomy of RAG/agent evaluation, reference-based vs. referenceless, LLM-as-judge and its failure modes, the code-vs-judge scorer decision in plain language, the DeepEval/RAGAS/MLflow/Arize tooling landscape, and a question → module/metric lookup table | ✅ Built |
| 1.1 | [`01_Retrieval_Metrics_Deterministic.ipynb`](01_Retrieval_Metrics_Deterministic.ipynb) | Precision@K, Recall@K, MRR, nDCG — no API calls | ✅ Built (free to run) |
| 1.2 | [`02_Retrieval_Metrics_LLM_Judged.ipynb`](02_Retrieval_Metrics_LLM_Judged.ipynb) | Contextual Precision/Recall/Relevancy — condensed from the 3 `archive/labs-rag-evaluation/deepeval-metrics/` drill notebooks, hand-constructed test cases (no live-pipeline dependency) | ✅ Built (needs `OPENAI_API_KEY`) |
| 1.3 | [`03_Generator_Metrics_Referenceless.ipynb`](03_Generator_Metrics_Referenceless.ipynb) | Faithfulness, Answer Relevancy, Hallucination (DeepEval; RAGAS answer relevancy only through DeepEval's `RAGASAnswerRelevancyMetric` wrapper) | ✅ Built (needs `OPENAI_API_KEY`) |
| 1.4 | [`04_Generator_Metrics_Reference_Based.ipynb`](04_Generator_Metrics_Reference_Based.ipynb) | Answer Correctness (custom `GEval`, both `criteria`- and `evaluation_steps`-based), Answer Semantic Similarity | ✅ Built (needs `OPENAI_API_KEY`) |
| 1.5 | [`05_RAG_Eval_Inside_the_Pipeline.ipynb`](05_RAG_Eval_Inside_the_Pipeline.ipynb) | Evaluation wired in as LangGraph nodes — mocked (free) then real (needs `OPENAI_API_KEY`) | ✅ Built |
| 1.6 | [`06_RAGAS_in_Practice.ipynb`](06_RAGAS_in_Practice.ipynb) | RAGAS quickstart + multi-metric example + the pytest/Excel/live-backend CI pattern | ✅ Built (needs `OPENAI_API_KEY`) |
| 1.7 | [`07_RAG_Capstone_Build_and_Evaluate.ipynb`](07_RAG_Capstone_Build_and_Evaluate.ipynb) | Build a real RAG system (Chroma + the phase's shared dataset), synthesize a golden dataset, run the full metric suite end-to-end | ✅ Built (needs `OPENAI_API_KEY`; data-loading path verified) |
| 2.1 | [`08_MultiTurn_Conversational_Evaluation.ipynb`](08_MultiTurn_Conversational_Evaluation.ipynb) | `ConversationalGEval`, `TurnRelevancyMetric`, `KnowledgeRetentionMetric`, conversation simulation | ✅ Built (needs `OPENAI_API_KEY`) |
| 2.2 | [`09_Tool_Use_Evaluation.ipynb`](09_Tool_Use_Evaluation.ipynb) | `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ToolUseMetric` | ✅ Built (needs `OPENAI_API_KEY`) |
| 2.3 | [`10_Task_Completion_Evaluation.ipynb`](10_Task_Completion_Evaluation.ipynb) | `TaskCompletionMetric`, custom `GEval` rubrics, outcome verification | ✅ Built (needs `OPENAI_API_KEY`) |
| 2.4 | [`11_Same_Evals_with_MLflow.ipynb`](11_Same_Evals_with_MLflow.ipynb) | Modules 2.1–2.2's questions, reimplemented via `mlflow.genai.evaluate()` (`Guidelines`, `make_judge`, `@scorer` over `Trace`/`SpanType.TOOL`) | ✅ Built (needs `OPENAI_API_KEY`; local SQLite MLflow store) |
| 3 | [`12_Agent_Trajectory_Evaluation.ipynb`](12_Agent_Trajectory_Evaluation.ipynb) | Simple mocked trajectory scoring, then the full 9-metric trace-level suite (mocked, free) on a realistic refund-agent scenario + Databricks mapping table, then a real tool-calling agent (needs `OPENAI_API_KEY`) | ✅ Built (Parts A–B free; Part C needs `OPENAI_API_KEY`) |
| 4 | [`13_Production_Grade_Agent_Eval_Overview.ipynb`](13_Production_Grade_Agent_Eval_Overview.ipynb) | Arize Phoenix end to end on a small support agent: tracing, router and skill evals logged onto spans, the convergence score, an experiment comparing two prompts | Needs the `phoenix` extra and `phoenix serve` |
| 5 | [`14_Capstone_CrewAI_Travel_Planner_Eval.ipynb`](14_Capstone_CrewAI_Travel_Planner_Eval.ipynb) | `TaskCompletionMetric` (Module 2.3) batch-scored against a real running 3-agent CrewAI app, left in place at `labs/agent-evaluation/crewai-travel-planner/` | ✅ Built (walkthrough; app is a separate live process — see notebook's Standing up the app) |

**If you only have an hour:** Module 0 → 1.2 → 2.2 → 3.

## Related, but out of scope for this tutorial

- Adversarial/safety testing answers "can this be made to misbehave?", a different question from the quality evaluation covered here. The `deepteam` red-teaming notebooks stayed in the old monorepo; in this repo, [`07_safety_and_policy_checks.ipynb`](../03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) in course 03 covers deterministic safety and policy checks inside a harness.
