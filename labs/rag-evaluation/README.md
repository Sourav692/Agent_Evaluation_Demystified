# RAG Evaluation

**Canonical lesson:** course 01 notebooks `02`–`04`, `06` and `07`
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)).
This folder is the raw material they were distilled from. `ragas-scripts/Evaluate_RAG_PyTest.py`
and `test_questions.xlsx` are driven by notebook `06`.

The original RAG evaluation material — retriever metrics, generator metrics, custom
LLM-as-judge rubrics, and a full build-then-evaluate pipeline, plus DeepEval metric drills
and RAGAS scripts.

**Distilled into:** course 01 module 1
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)),
which condenses the drills and rewires the examples to run standalone. Come here for the
unabridged version, or when a course notebook points at one of these.

## Notebooks

| Notebook | Topic | Runs standalone? |
|---|---|---|
| `1.Retriever_Evaluation_Metrics.ipynb` | Contextual Precision / Recall / Relevancy against a live pipeline | no — opens with `%run Build_RAG_Pipeline_with_Source.ipynb` |
| `2.Generator_Evaluation_Metrics.ipynb` | Faithfulness, Answer Relevancy, Hallucination — DeepEval and RAGAS side by side | no — same `%run` |
| `3.Custom_LLM_as_a_Judge_(G-Eval).ipynb` | Why Answer Correctness needs a custom `GEval` rubric | no — same `%run` |
| `4.End_to_End_RAG_System_Evaluation.ipynb` | Synthesize a golden dataset, then run the full retriever + generator suite | needs an older `deepeval` — see note below |
| `Build_RAG_Pipeline_with_Source.ipynb` | The pipeline the three notebooks above `%run`. Persists a Chroma store to `my_db/` (gitignored) | yes |

## Subfolders

| Path | Contents |
|---|---|
| `deepeval-metrics/` | Standalone drills for Contextual Precision, Recall and Relevancy — each runs the same metric across 8–10 near-identical examples. Course 01 module 1.2 keeps the 2–3 per metric that teach something distinct. |
| `ragas-scripts/` | RAGAS as scripts rather than notebooks: `Faithfulness.py`, `ContextRecall.py`, `Evaluate_RAG.py`, a pytest-based CI pattern (`Evaluate_RAG_PyTest.py`), and a Streamlit front end |
| `fastapi-rag-bot/` | A small FastAPI RAG service used as an evaluation target, with a Streamlit client |

## Notes

- **`4.End_to_End_RAG_System_Evaluation.ipynb` targets an older DeepEval.** It calls
  `Synthesizer(model=..., embedder=...)` then `.generate_goldens(contexts=..., evolutions=...)`.
  In `deepeval>=4.1.8` (this repo's pin) `embedder` is gone, the method is
  `generate_goldens_from_contexts(...)`, and `evolutions`/`scenario`/`task` moved into
  `EvolutionConfig`/`StylingConfig` constructor objects. Course 01 module 1.7 has the
  updated version.
- Streamlit demos need `pip install -e '.[apps]'`.
