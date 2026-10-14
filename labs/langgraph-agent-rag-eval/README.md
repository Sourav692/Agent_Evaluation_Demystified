# LangGraph Agent & RAG Evaluation

**Canonical lesson:** course 01 notebooks `01`, `04`, `05` and `12`
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)).
These notebooks are their unabridged sources, kept for the end-to-end version.

Interview-prep notebooks that evaluate LangGraph-based RAG and agent systems. Where the
courses teach one idea per notebook, these run the whole surface end to end.

| Notebook | What it is | Runs offline? |
|---|---|---|
| `rag_agent_eval_langgraph_new.ipynb` | The fullest mocked version: retrieval metrics, in-pipeline evaluation, and a **9-metric trace-level agent suite** (tool selection, argument correctness, redundant calls, step-wise accuracy, task success, fuzzy trajectory match, end-state verification, recovery rate, cost proxy) plus a Databricks production-mapping table | yes |
| `rag_agent_eval_langgraph_openai.ipynb` | The same ground against live OpenAI calls and a real tool-calling agent | needs `OPENAI_API_KEY` |

`_new` and `_openai` are the two to read; the first is a strict subset of `_new`.

**Distilled into:** course 01 modules 1.1, 1.5 and 3
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)).
The 9-metric suite is reproduced there in full — this folder is the original.

The earliest draft, `rag_agent_eval_langgraph.ipynb`, is a strict subset of `_new` and moved to
[`../../archive/labs-langgraph-agent-rag-eval/`](../../archive/labs-langgraph-agent-rag-eval/).
