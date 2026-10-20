# 04 — End-to-End Evaluation Tutorial

**One support-desk agent, evaluated end to end: retrieval, generation, tool calls, trajectories,
safety, judges, statistics, a CI release gate, and online evaluation.** The metrics come from
open-source frameworks (RAGAS, DeepEval, DeepTeam, `ranx`); traces, datasets and experiments live
in LangSmith.

The goal is the whole picture of how evaluation works, not Python. Code is kept deliberately
simple and the comments explain the evaluation, not the syntax.

---

## Status

| Notebooks | State |
|---|---|
| 01–02 | Written and run, outputs kept: the app under test (RAG agent, tools, supervisor graph) |
| 03 | Written and run: the golden set, 121 cases in 6 slices → `data/golden_set.json` |
| 04–05 | Written and run: retrieval and generation evaluation → `data/rag_scores.json`. Notebook 04 records the baseline run, `data/golden_runs.json`, that 04–09 all score |
| 06–08 | Written and run: tool calls, trajectories and routing, task completion and conversations → `data/agent_scores.json` |
| 09 | Written and run: safety and red-teaming → `data/safety_scores.json` |
| 10–14 | Planned |

---

## How this course is built

- **Each notebook stands alone.** Open any one and run it top to bottom. Notebooks hand results to
  each other through files in `data/`; if an input file is missing, the notebook says which
  notebook writes it.
- **No shared modules.** Helpers are repeated in each notebook that needs them, on purpose. The
  only script is the release gate, because CI has to run a file.
- **Outputs are committed.** Runs call the paid OpenAI API, so you can read every result without
  running anything.

---

## Stack

| Layer | Tool |
|---|---|
| App under test | LangGraph supervisor: router, RAG agent, account-tools agent, escalation |
| Models | App (the agent under test): `deepseek-ai/DeepSeek-V4-Flash-0731` on Nebius Token Factory. Judge: `Qwen/Qwen3-235B-A22B-Instruct-2507` on Nebius Token Factory. OpenAI: embeddings `text-embedding-3-small`, simulated customers and attack writers `gpt-4o-mini`, the cached RAGAS test-set generator `gpt-4o` |
| Vector store | Chroma |
| Metrics | stdlib, `ranx`, RAGAS, DeepEval, DeepTeam |
| Traces, datasets, experiments, labels, online scoring | LangSmith (free Developer plan) |
| Optional open-source alternative | Langfuse (a separate optional track, planned) |
| Release gate | stdlib gate script in GitHub Actions |

---

## Notebooks

| # | Notebook | Evaluates |
|---|---|---|
| 01 | Knowledge base and RAG agent | — builds the RAG half |
| 02 | Tools, agents and the supervisor graph | — builds the agent half, writes `data/agent_runs.json` |
| 03 | The golden set | Test-set quality |
| 04 | Retrieval evaluation | Recall@k, MRR, nDCG; judged context precision/recall |
| 05 | Generation evaluation | Faithfulness, relevancy, correctness; retriever-vs-generator blame |
| 06 | Tool-call evaluation | Tool selection, arguments, abstention |
| 07 | Trajectories and handoffs | Path match, efficiency, routing, context preservation |
| 08 | Task completion and conversations | End state, task completion, multi-turn metrics |
| 09 | Safety and red-teaming | Injection, jailbreak, PII, excessive agency |
| 10 | Custom judges | `GEval`, `DAGMetric`, pairwise |
| 11 | Calibrating judges with human labels | Kappa, TPR/TNR, judge bias |
| 12 | Statistics, cost and experiments | Slices, CIs, paired tests, LangSmith experiments |
| 13 | The release gate and CI | Gate rules, free vs paid CI jobs |
| 14 | Online evaluation and the loop | Live trace scoring, drift, feedback to the golden set |

---

## Setup

```bash
cd courses/04-end-to-end-eval-tutorial
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m ipykernel install --user --name end-to-end-eval-tutorial \
    --display-name "Course 04 — End-to-End Eval"
```

Pick the **Course 04 — End-to-End Eval** kernel in Jupyter. Always pass `--python` to
`uv pip install`: the repository root sets `VIRTUAL_ENV`, which would otherwise receive the install.

Environment variables, in the repository-root `.env` (see `.env.example`):

| Variable | Where to get it |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com (embeddings, simulators, the test-set generator) |
| `NEBIUS_API_KEY` | tokenfactory.nebius.com → API keys (the app model and the judge) |
| `LANGSMITH_API_KEY` | A free Developer account at smith.langchain.com → Settings → API Keys |
| `LANGSMITH_PROJECT` | `end-to-end-eval-tutorial` (the tracing project the notebooks write to) |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com`, or `https://eu.api.smith.langchain.com` for an EU workspace |

The notebooks set `LANGSMITH_TRACING=true` themselves, so other courses that read the same
`.env` don't start tracing.

**Models on Nebius:** both models are reached through Nebius Token Factory's OpenAI-compatible
API (`https://api.tokenfactory.nebius.com/v1`): the app with `ChatOpenAI`, the judge with
DeepEval's `GPTModel(base_url=...)` and RAGAS's `llm_factory` on an `AsyncOpenAI` client. The base
URL is passed to those clients only, never set as `OPENAI_BASE_URL`, so embeddings stay on OpenAI.
Nebius serves each model from one deployment (fp8), so every run hits the same model. The app is a
reasoning model, so its reasoning is set explicitly: `"none"` wherever a plain answer must be
parsed, `"low"` for the tool-calling agent. The judge is an instruct model with no thinking, run
at `temperature=0`. Limits: 1M tokens and 3,000 requests a minute for the app, 400K and 600 for the
judge; the clients retry on 429.

**LangSmith free-plan limits that affect this course:** 5k traces a month (one agent run is one
trace; a 120-case pass is 120), traces kept 14 days, one seat, no self-hosting. Results the
notebooks need later are saved to `data/`, so they survive the 14-day expiry.

**Optional Langfuse track.** Langfuse is the open-source, self-hostable alternative. Its keys
(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) are listed in `.env.example`
and its pin is commented in `requirements.txt`; the Langfuse notebooks are planned for later.

---

## Cost

> **Models changed (2026-10-20):** the app runs on `deepseek-ai/DeepSeek-V4-Flash-0731` ($0.14 / $0.28 per
> million input / output tokens) and the judge on `Qwen/Qwen3-235B-A22B-Instruct-2507` ($0.20 / $0.60),
> both on Nebius Token Factory. Both are cheaper than the `gpt-4o-mini` / `gpt-4o` pair the costs below
> were measured with, so treat the table as an upper bound until it is re-measured.

Approximate cost of one full run per notebook (01–09 measured as estimates from the 2026-10-19 runs; 10–14 still planned figures), assuming a 120-case golden set (6 slices × 20) and
mid-2026 list prices (`gpt-4o-mini` $0.15 / $0.60, `gpt-4o` $2.50 / $10 per million input /
output tokens). Re-measure from LangSmith's cost tracking once the notebooks exist.

| Notebook | Main cost | ≈ USD |
|---|---|---|
| 01–02 | Embedding the KB, 5 smoke questions | < 0.10 |
| 03 | RAGAS test-set generation (`gpt-4o`); cached after the first run | ~0.50 |
| 04 | Baseline run (cached) + judged retrieval, two frameworks | ~1.50 |
| 05 | Judged generation metrics, two frameworks | ~3 |
| 06 | Argument-correctness judge | < 0.50 |
| 07 | Trajectory and context-preservation judges | < 0.50 |
| 08 | Task-completion judges + simulator + 4 conversational metrics | ~1.50 |
| 09 | DeepTeam attacks + safety rubric | ~0.80 |
| 10 | Three custom judges + pairwise | ~6 |
| 11 | Bias re-runs of judges | ~3 |
| 12 | Baseline + candidate experiments | ~10 |
| 13 | Gate itself free; each manual `evaluate` run ≈ notebook 12 | 0 / ~10 |
| 14 | 200 simulated traces, 10% judged | ~1 |
| **Total** | | **≈ 30–35** |

Notebooks 04–05 are the biggest lever: running both RAGAS and DeepEval on a 20-case subset, and
one framework on the full set, roughly halves their cost.
