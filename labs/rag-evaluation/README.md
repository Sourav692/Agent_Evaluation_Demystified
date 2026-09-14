# RAG Evaluation

**Status:** ✅ Built.

Core notebooks merged from `RAG_Demystified`'s "Evaluating RAG Systems" section. DeepEval metric drills and RAGAS scripts added from `Agents_Evaluation_Demystified` (the source's `Evaluating RAG Systems/` folder was skipped — three notebooks identical to the ones already here, two older unexecuted copies of the same retriever/generator notebooks).

| Path | Topic |
|---|---|
| `labs/rag-evaluation/1.Retriever_Evaluation_Metrics.ipynb` | Retriever evaluation metrics |
| `labs/rag-evaluation/2.Generator_Evaluation_Metrics.ipynb` | Generator evaluation metrics |
| `labs/rag-evaluation/3.Custom_LLM_as_a_Judge_(G-Eval).ipynb` | Custom LLM-as-judge (G-Eval) |
| `labs/rag-evaluation/4.End_to_End_RAG_System_Evaluation.ipynb` | End-to-end RAG evaluation |
| `labs/rag-evaluation/Build_RAG_Pipeline_with_Source.ipynb` | Supporting pipeline used by the evaluation notebooks |
| `DeepEval_Metrics/` | Standalone DeepEval drills: contextual precision, recall, relevancy |
| `RAGAS/` | RAGAS scripts + a small FastAPI/Streamlit RAG bot used as the eval target |

Additional RAG evaluation notebooks/scripts also live inside `08_Advanced_RAG/Comprehensive_RAG_Techniques/evaluation/` (kept there rather than split out, since they share that collection's `helper_functions.py`/`data/`).
