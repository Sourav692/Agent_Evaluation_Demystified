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
| 06 | Written and run: tool calls → `data/agent_scores.json`. Outputs not saved in the notebook; re-run to see them |
| 07–08 | Written and run: trajectories and routing, task completion and conversations → `data/agent_scores.json` |
| 09 | Written and run: safety and red-teaming → `data/safety_scores.json` |
| 10 | Written and run: custom judges → `data/custom_judge_scores.json` |
| 11 | Written, not run: judge calibration → `data/judge_trust.json`, once a person has labelled the sample |
| 12 | Written and run: statistics, cost and LangSmith experiments → `data/baseline_scores.json`, `data/candidate_scores.json` |
| 13 | Written and run: the release gate (`gate.py`, `gate_rules.json`) and `.github/workflows/course04-release-gate.yml`; the gate passes the real candidate and refuses a synthetic seeded regression |
| 14 | Written and run: online evaluation and the loop → `data/online_review_queue.json`, `data/golden_set_candidates.json` |

The whole course, notebook by notebook, with the topics each part covers:
[`COURSE.md`](COURSE.md) ([browser version](COURSE.html)).

How the course is being built: [`PLAN.md`](PLAN.md) records the stack decisions,
[`EVALUATIONS.md`](EVALUATIONS.md) specifies every evaluation and its metric, and
[`TRACKER.md`](TRACKER.md) tracks the build task by task.

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
| Models | All set in [`models.toml`](models.toml), all on OpenRouter: app (the agent under test) `deepseek/deepseek-v4-flash-0731`, judge `qwen/qwen3-235b-a22b-2507`, embeddings `openai/text-embedding-3-small`, simulated customers and attack writers `openai/gpt-4o-mini`, the cached RAGAS test-set generator `openai/gpt-4o`. Moderation (`omni-moderation-latest`) stays on OpenAI |
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
| `OPENROUTER_API_KEY` | openrouter.ai/keys (every model in `models.toml`) |
| `OPENAI_API_KEY` | platform.openai.com (notebook 09's moderation call only; OpenRouter has no moderation endpoint) |
| `LANGSMITH_API_KEY` | A free Developer account at smith.langchain.com → Settings → API Keys |
| `LANGSMITH_PROJECT` | `end-to-end-eval-tutorial` (the tracing project the notebooks write to) |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com`, or `https://eu.api.smith.langchain.com` for an EU workspace |

The notebooks set `LANGSMITH_TRACING=true` themselves, so other courses that read the same
`.env` don't start tracing.

**Models are config-driven:** [`models.toml`](models.toml) names every model and its provider.
To change one, edit that file only; no notebook names a model, URL or key. A role (`app`, `judge`,
`embedding`, `generator`, `simulator`, `moderation`) picks a provider; the provider gives the
OpenAI-compatible base URL and the `.env` variable that holds its key. Each notebook's setup cell
reads the file with `tomllib` through a small `model_config(role)` helper, repeated per notebook
like the course's other helpers. The base URL is passed to each client, never set as
`OPENAI_BASE_URL`. A role's `extra_body` is sent with every request: on OpenRouter it pins one
provider (`allow_fallbacks = false`), so every run hits the same deployment at the same precision.
The app is a reasoning model, so its reasoning is set in the config: `"none"` wherever a plain
answer must be parsed, `"low"` for the tool-calling agent. The judge is an instruct model with no
thinking, run at `temperature=0`; the clients retry on 429. After changing the app model, delete
`data/golden_runs.json`; after changing the embedding model, rebuild `data/chroma_db/` with notebook 01.

**LangSmith free-plan limits that affect this course:** 5k traces a month (one agent run is one
trace; a 120-case pass is 120), traces kept 14 days, one seat, no self-hosting. Results the
notebooks need later are saved to `data/`, so they survive the 14-day expiry.

**Optional Langfuse track.** Langfuse is the open-source, self-hostable alternative. Its keys
(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) are listed in `.env.example`
and its pin is commented in `requirements.txt`; the Langfuse notebooks are planned for later.

---

## Cost

Nothing here has been measured yet. Both columns are estimates of one full run per notebook,
assuming a 120-case golden set (6 slices × 20).

- **Original estimate:** made on 2026-10-19 for the first model pair, `gpt-4o-mini` as the app
  ($0.15 / $0.60 per million input / output tokens) and `gpt-4o` as the judge ($2.50 / $10).
  It predates the change that runs RAGAS on a 20-case subset only, so 04–05 are high.
- **Current models:** the app is `deepseek-ai/DeepSeek-V4-Flash-0731` ($0.14 / $0.28) and the
  judge `Qwen/Qwen3-235B-A22B-Instruct-2507` ($0.20 / $0.60), on Nebius Token Factory from
  2026-10-20, on OpenRouter since 2026-11-18 (same models; prices per `list-model-endpoints`). This column scales the judge share of each row by the price ratio (about 12–17×
  cheaper) and keeps the OpenAI calls at their old price: embeddings, the `gpt-4o-mini` simulated
  customers and attack writers, the `gpt-4o` test-set generator in 03 and the `gpt-4o`
  reference judge in 11. The range allows for the Qwen judge's occasional retries
  (`LengthFinishReasonError` at its 8,192-token limit).

| Notebook | Main cost | ≈ USD, original estimate | ≈ USD, current models |
|---|---|---|---|
| 01–02 | Embedding the KB, 5 smoke questions | < 0.10 | < 0.10 |
| 03 | RAGAS test-set generation (`gpt-4o`); cached after the first run | ~0.50 | ~0.50 |
| 04 | Baseline run (cached) + judged retrieval, two frameworks | ~1.50 | ~0.20 |
| 05 | Judged generation metrics, two frameworks | ~3 | ~0.30 |
| 06 | Argument-correctness judge | < 0.50 | < 0.05 |
| 07 | Trajectory and context-preservation judges | < 0.50 | < 0.05 |
| 08 | Task-completion judges + simulator + 4 conversational metrics | ~1.50 | ~0.30 |
| 09 | DeepTeam attacks + safety rubric | ~0.80 | ~0.30 |
| 10 | Three custom judges + pairwise | ~6 | ~0.50 |
| 11 | Bias re-runs of judges + `gpt-4o` reference judge on the calibration subset | ~3 | ~1.30 |
| 12 | Baseline + candidate experiments | ~10 | ~1 |
| 13 | Gate itself free; each manual `evaluate` run ≈ notebook 12 | 0 / ~10 | 0 / ~1 |
| 14 | 200 simulated traces, 10% judged | ~1 | ~0.20 |
| **Total** | | **≈ 30–35** | **≈ 5–10** |

Notebooks 01–09 have already run, so on current models about $3–6 of the total is still to
spend, in 10–14. For actual spend, read the OpenRouter activity page (and the Nebius billing page for
runs before 2026-11-18). LangSmith traces only the app's runs, not the judge calls (P0.12), and notebook 12
(§16 in `EVALUATIONS.md`) is where cost gets measured per case.
