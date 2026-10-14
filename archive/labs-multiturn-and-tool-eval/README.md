# Multi-turn & Tool Evaluation

Three questions — did the conversation hold together, did the agent call the right tool
with the right arguments, did the task actually complete — answered **twice**: once with
DeepEval, once with MLflow's eval APIs, as a direct framework comparison.

| File | What it is |
|---|---|
| `evaluation.ipynb` | DeepEval: `ConversationalGEval`, `TurnRelevancyMetric`, `KnowledgeRetentionMetric`, then `ToolCorrectnessMetric` / `ArgumentCorrectnessMetric` / `ToolUseMetric`, then `TaskCompletionMetric` |
| `mlflow_evaluation.ipynb` | The same three areas via `mlflow.genai.evaluate()` — `Guidelines`, `make_judge`, `@scorer` over `Trace` / `SpanType.TOOL` |
| `test_conv.py` | Multi-turn conversational evaluation as a runnable script |
| `test_tools1.py` · `test_tools2.py` · `test_tools3.py` | Tool-use evaluation, one metric per script |

**Distilled into:** course 01 modules 2.1–2.4
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)),
where module 2.4 keeps the MLflow comparison deliberately adjacent to the DeepEval versions.

## Setup

> **This lab has its own environment.** It pins `deepeval==3.8.8`, older than the repo
> root's `>=4.1.8`. Run it here, not from the root venv.

```bash
cd labs/multiturn-and-tool-eval
uv sync
python test_conv.py      # or test_tools1.py, test_tools2.py, test_tools3.py
```

Python 3.12 (see `.python-version`).

## LLM provider

By default this project points `OPENAI_API_KEY` at **OpenRouter** via an alternative base
URL (`https://openrouter.ai/api/v1`). To use OpenAI directly, supply an OpenAI key and the
standard base URL.

Either way, use OpenAI **models** — DeepEval's metric defaults assume them, and swapping
the underlying model changes the scores.
