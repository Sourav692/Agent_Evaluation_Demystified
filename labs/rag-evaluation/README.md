# RAG Evaluation

**Canonical lesson:** course 01 notebooks `02`–`04`, `06` and `07`
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)).
What is left here is the part a course notebook drives rather than repeats: a live RAG
service to evaluate, and the pytest pattern that scores it.

| Path | Contents |
|---|---|
| `fastapi-rag-bot/` | A small FastAPI RAG service (`POST /upload`, `POST /ask`) used as an evaluation target, with a Streamlit client (`streamlit_app.py`) |
| `ragas-scripts/Evaluate_RAG_PyTest.py` + `test_questions.xlsx` | The batch/CI pattern: one pytest case per spreadsheet row, each calling the live bot and scoring the answer with RAGAS. Course 01 notebook `06` walks through it (updated to the RAGAS 0.4 API there; this script still uses the 0.3 one) |
| `ragas-scripts/Streamlit_RAG_Ragas.py` | A Streamlit RAG demo with RAGAS scoring |

**Needs:** `OPENAI_API_KEY`; `pip install -e '.[apps]'` for the Streamlit apps. Every script
calls a paid model.

The original notebooks — retriever and generator metrics, the custom G-Eval rubric, the
build-then-evaluate pipeline, the DeepEval metric drills and the single-metric RAGAS scripts —
moved to [`../../archive/labs-rag-evaluation/`](../../archive/labs-rag-evaluation/) once course 01
carried everything in them.
