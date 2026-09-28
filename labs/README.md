# Labs

Raw source material. Runnable, but **not a curriculum** — these are the unabridged
originals that [`../courses/`](../courses/) was distilled from, plus vendor course
material kept whole.

Reach for a lab when a course notebook points at one, or when you want the full
version of something a course condensed.

| Lab | Contents | Needs |
|---|---|---|
| [`rag-evaluation/`](rag-evaluation/) | DeepEval metric drills (Contextual Precision/Recall/Relevancy), RAGAS scripts including a pytest-CI pattern, a build-a-RAG-pipeline notebook, a FastAPI RAG bot + Streamlit front end | `OPENAI_API_KEY`; `.[apps]` for Streamlit |
| [`agent-evaluation/arize-phoenix-labs/`](agent-evaluation/arize-phoenix-labs/) | DeepLearning.AI × Arize, 5 progressive labs: build an agent → trace it → router/skill judges → trajectory experiments → structured evaluation | `.[phoenix]`, `PHOENIX_COLLECTOR_ENDPOINT` |
| [`agent-evaluation/crewai-travel-planner/`](agent-evaluation/crewai-travel-planner/) | A real 3-agent CrewAI app behind FastAPI, with a pytest `TaskCompletionMetric` suite driven from Excel | `.[crewai]`, `SERPER_API_KEY` |
| [`agent-evaluation/multi-agent-eval-demo/`](agent-evaluation/multi-agent-eval-demo/) | A tiny LangGraph supervisor team (calculator + writer) with a case dataset, checkable scores and an LLM judge, behind FastAPI and a Streamlit scorecard | its own `requirements.txt`, `OPENAI_API_KEY` |
| [`langgraph-agent-rag-eval/`](langgraph-agent-rag-eval/) | Interview-prep notebooks: deterministic retrieval metrics, a mocked RAG-eval graph, and a 9-metric trace-level agent suite | `OPENAI_API_KEY` (the `_openai` notebook only) |
| [`multiturn-and-tool-eval/`](multiturn-and-tool-eval/) | Multi-turn conversational, tool-use and task-completion metrics — once in DeepEval, once in MLflow, as a direct comparison | Its own `uv` project: `cd` in and `uv sync` |
| [`llm-as-judge/`](llm-as-judge/) | A DeepEval G-Eval smoke test | `OPENAI_API_KEY` |

> `multiturn-and-tool-eval/` has its own `pyproject.toml` and `uv.lock` and pins an older
> DeepEval than the repo root. Run it in its own environment.
