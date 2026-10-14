# RAG evaluation techniques

**Unique:** judge meta-evaluation (GroUSE), nugget- and citation-level metrics (Open-RAG-Eval)
and completeness. Course 01 covers the core metrics; these three notebooks go past them.

Five standalone notebooks on evaluating a RAG system, each with a different tool. They are the
evaluation section of Nir Diamant's *RAG_Techniques* anthology, moved here on 2026-09-29 from
`AI-ENGINEERING-DEMYSTIFIED` (tag `pre-multirepo-split-2026-09`,
`03_Advanced/08_Advanced_RAG/Comprehensive_RAG_Techniques/evaluation/`) when that monorepo was split
into per-topic repositories — evaluation curricula live in this repository.

| Notebook | Tool | What it evaluates |
|---|---|---|
| [`define_evaluation_metrics.ipynb`](define_evaluation_metrics.ipynb) | LangChain evaluators | Defining correctness, faithfulness and relevance criteria for RAG answers |
| [`end-2-end_rag_evaluation.ipynb`](end-2-end_rag_evaluation.ipynb) | RAGAS | End-to-end RAG evaluation over a generated test set |
| [`evaluation_deep_eval.ipynb`](evaluation_deep_eval.ipynb) | DeepEval | Correctness, faithfulness and contextual relevancy test cases |
| [`evaluation_grouse.ipynb`](evaluation_grouse.ipynb) | GroUSE | Grounded-QA evaluation with GroUSE judge tests (diagram in `images/`) |
| [`open-rag-eval-example.ipynb`](open-rag-eval-example.ipynb) | Open-RAG-Eval | Vectara's Open-RAG-Eval metrics, results table and summary plot |

**Needs:** `OPENAI_API_KEY`. Every notebook calls a paid judge model — don't run them unless you
mean to spend credits.

**Environment caveats (unchanged from the source):**
- `define_evaluation_metrics` uses LangChain 0.x import paths (`langchain.evaluation`,
  `langchain_core.pydantic_v1`, …) that don't exist under LangChain 1.x.
- `evaluation_grouse` and `open-rag-eval-example` each need their own environment; their pins are in
  [`requirements-grouse.txt`](requirements-grouse.txt) and
  [`requirements-open-rag-eval.txt`](requirements-open-rag-eval.txt).
- `end-2-end_rag_evaluation` imports `ChatOpenAI` from `langchain.chat_models`, a LangChain 0.x path;
  under LangChain 1.x use `from langchain_openai import ChatOpenAI` instead.
- `open-rag-eval-example` writes `evaluation_results.csv` and `metrics_summary.png` next to itself.

**Licence:** these notebooks stay under the anthology's own non-commercial licence — see
[`LICENSE`](LICENSE) — not this repository's licence.
