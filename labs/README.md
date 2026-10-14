# Labs

Raw source material. Runnable, but **not a curriculum** — these are the unabridged
originals that [`../courses/`](../courses/) was distilled from, plus vendor course
material kept whole.

Reach for a lab when a course notebook points at one, or when you want the full
version of something a course condensed.

| Lab | Contents | Needs |
|---|---|---|
| [`rag-evaluation/`](rag-evaluation/) | The RAGAS pytest-CI script course 01 notebook 06 drives, a FastAPI RAG bot + Streamlit front end | `OPENAI_API_KEY`; `.[apps]` for Streamlit |
| [`rag-evaluation-techniques/`](rag-evaluation-techniques/) | Three standalone RAG-evaluation notebooks from Nir Diamant's *RAG_Techniques* anthology: RAGAS end to end, GroUSE, Open-RAG-Eval (non-commercial licence, kept alongside) | `OPENAI_API_KEY`; GroUSE needs its own env |
| [`agent-evaluation/crewai-travel-planner/`](agent-evaluation/crewai-travel-planner/) | A real 3-agent CrewAI app behind FastAPI, with a pytest `TaskCompletionMetric` suite driven from Excel | `.[crewai]`, `SERPER_API_KEY` |
| [`agent-evaluation/multi-agent-eval-demo/`](agent-evaluation/multi-agent-eval-demo/) | A tiny LangGraph supervisor team (calculator + writer) with a case dataset, checkable scores and an LLM judge, behind FastAPI and a Streamlit scorecard | its own `requirements.txt`, `OPENAI_API_KEY` |
| [`langgraph-agent-rag-eval/`](langgraph-agent-rag-eval/) | Interview-prep notebooks: deterministic retrieval metrics, a mocked RAG-eval graph, and a 9-metric trace-level agent suite | `OPENAI_API_KEY` (the `_openai` notebook only) |

> Superseded labs — the multi-turn/tool lab, the G-Eval smoke test, the RAG metric drills and
> early notebook drafts — moved to [`../archive/`](../archive/) once course 01 carried everything in them.
