# RAG evaluation techniques

**Unique:** judge meta-evaluation (GroUSE), nugget- and citation-level metrics (Open-RAG-Eval)
and completeness. Course 01 covers the core metrics; these three notebooks go past them.

Three standalone notebooks on evaluating a RAG system, each with a different tool. They are the
evaluation section of Nir Diamant's *RAG_Techniques* anthology, moved here on 2026-09-29 from
`AI-ENGINEERING-DEMYSTIFIED` (tag `pre-multirepo-split-2026-09`,
`03_Advanced/08_Advanced_RAG/Comprehensive_RAG_Techniques/evaluation/`) when that monorepo was split
into per-topic repositories — evaluation curricula live in this repository.

| Notebook | Tool | What it evaluates |
|---|---|---|
| [`end-2-end_rag_evaluation.ipynb`](end-2-end_rag_evaluation.ipynb) | RAGAS | End-to-end RAG evaluation over a generated test set |
| [`evaluation_grouse.ipynb`](evaluation_grouse.ipynb) | GroUSE | Grounded-QA evaluation with GroUSE judge tests (diagram in `images/`) |
| [`open-rag-eval-example.ipynb`](open-rag-eval-example.ipynb) | Open-RAG-Eval | Vectara's Open-RAG-Eval metrics, results table and summary plot |

**Needs:** `OPENAI_API_KEY`. Every notebook calls a paid judge model — don't run them unless you
mean to spend credits.

**Environment caveats (unchanged from the source):**
- `evaluation_grouse` and `open-rag-eval-example` each need their own environment; their pins are in
  [`requirements-grouse.txt`](requirements-grouse.txt) and
  [`requirements-open-rag-eval.txt`](requirements-open-rag-eval.txt).
- `end-2-end_rag_evaluation` imports `ChatOpenAI` from `langchain.chat_models`, a LangChain 0.x path;
  under LangChain 1.x use `from langchain_openai import ChatOpenAI` instead.
- `open-rag-eval-example` writes `evaluation_results.csv` and `metrics_summary.png` next to itself.

**Licence:** these notebooks stay under the anthology's own non-commercial licence — see
[`LICENSE`](LICENSE) — not this repository's licence.

Two more notebooks from the same anthology — `evaluation_deep_eval.ipynb` (a third telling of
course 01's DeepEval metrics) and `define_evaluation_metrics.ipynb` (hand-written judge prompts,
broken on LangChain 1.x) — moved to
[`../../archive/labs-rag-evaluation-techniques/`](../../archive/labs-rag-evaluation-techniques/), with a copy of the licence.
Its few-shot judge-prompt idea is now in course 03 notebook 08.
