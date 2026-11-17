# Open-Source Agent & RAG Eval Tutorial — Stack Plan

2026-10-18 · Sourav Banerjee

The tutorial runs the whole evaluation loop on open-source frameworks, from building the agent to
gating its release. Each stage below lists the options: fill **Your pick** with `Use`, `Maybe`
or `Skip`, and write your own idea in the **Your suggestion** line under the table.

**Model decision (2026-10-18):** open-source frameworks, OpenAI models. Every LLM call (app,
judge, embeddings) goes to the OpenAI API, and nothing is downloaded or served locally. Rows that
needed a local model were removed from Stages 2, 3, 9 and 11.

**Superseded 2026-10-20:** the app now runs `deepseek-ai/DeepSeek-V4-Flash-0731` and the primary
judge is `Qwen/Qwen3-235B-A22B-Instruct-2507`, both on Nebius Token Factory. OpenAI stays for
embeddings, simulated customers, attack writers and the RAGAS test-set generator, and `gpt-4o`
runs as a reference judge on the calibration subset only. See [`TRACKER.md`](TRACKER.md), P6.10.

**Platform decision (2026-10-18):** LangSmith replaces Langfuse for traces, datasets, experiments,
labels and online evaluation (Stages 8, 10, 12). LangSmith is not open source; Langfuse stays as an
optional open-source track for later notebooks.

## Decisions to make first

These answers change most stages below, so settle them before the per-stage picks. Write
yours in the last column.

| # | Question                                                        | Options                                                                                                                          | Recommended                                                                  | Your answer                                    |
| - | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| 1 | Must the models be open too, or only the frameworks?            | A: open-weight models everywhere (Ollama or vLLM) · B: open frameworks, OpenAI as judge · C: open app model, OpenAI judge only | A: no paid API, so every notebook can run in CI                              | Use my current OpenAI gpt40 model.             |
| 2 | What does the tutorial's agent do?                              | Support desk over a docs knowledge base · travel planner · research assistant                                                  | Support desk: RAG, tool calls and handoffs in one app                        | Support desk (2026-10-18) |
| 3 | Where does it live in this repo?                                | New `courses/04-…` · course 03 rebuilt on open models · a standalone repo                                                   | New `courses/04-…`, so course 03 stays the OpenAI edition                 | `courses/04-end-to-end-eval-tutorial/` (2026-10-18) |
| 4 | What hardware must it run on?                                   | 16 GB laptop, CPU only · Apple Silicon, 32 GB · one 24 GB GPU                                                                  | 16 GB laptop with 7–8B models, 4-bit quantised                              | No need of Downloaded model. Use OpenAI Model. |
| 5 | Which OpenAI model runs the app? ("gpt40" read as one of these) | `gpt-4o-mini` (course 03's default) · `gpt-4o` · `gpt-4.1-mini`                                                          | `gpt-4o-mini`: cheap enough to run the full golden set often               | `gpt-4o-mini` (2026-10-18) |
| 6 | Which OpenAI model is the judge?                                | Same as the app · `gpt-4o` · `gpt-4.1`                                                                                     | `gpt-4o`: a stronger model than the app, so it is not grading its own work | `gpt-4o` (2026-10-18) |

**Your suggestion:**

## Stage 1 — The app under test

The agent being evaluated: a RAG node, a few tools, and a supervisor that hands off between
them. Its framework decides how easily traces and tool calls can be pulled out for scoring.

| Option     | Licence    | What it gives the tutorial                                                                              | Recommended | Your pick |
| ---------- | ---------- | ------------------------------------------------------------------------------------------------------- | ----------- | --------- |
| LangGraph  | MIT        | Explicit graph, so every node and handoff is a traceable step; already pinned in this repo (`1.2.11`) | Yes         |           |
| LlamaIndex | MIT        | Strongest RAG building blocks; agent workflows are newer                                                | Alt         |           |
| Haystack   | Apache 2.0 | Pipeline-first RAG, clean component boundaries                                                          |             |           |
| CrewAI     | MIT        | Role-based multi-agent; this repo already has a CrewAI target app                                       |             |           |
| smolagents | Apache 2.0 | Minimal code agents; small enough to read in one sitting                                                |             |           |
| PydanticAI | MIT        | Typed tool calls and outputs, which simplifies argument checks                                          |             |           |

**Your suggestion:** *Use LangGraph only.* 

## Stage 2 — LLM and judge models

Two roles: the model inside the app, and the model that grades it. Both are OpenAI models
(decisions 1 and 4). Make the judge stronger than the app, so it is not marking its own work;
Stage 10 still checks the judge against human labels.

| Option                           | Role      | Access            | What it gives the tutorial                                                                | Recommended | Your pick |
| -------------------------------- | --------- | ----------------- | ----------------------------------------------------------------------------------------- | ----------- | --------- |
| `gpt-4o-mini`                  | App model | OpenAI API (paid) | Course 03's default; reliable tool calling at low cost per run                            | Yes         |           |
| `gpt-4o`                       | App model | OpenAI API (paid) | Stronger app, about 16x the per-token cost of `gpt-4o-mini`                             |             |           |
| `gpt-4.1-mini`                 | App model | OpenAI API (paid) | Long context and good instruction following; course 03 uses it in places                  | Alt         |           |
| `gpt-4o`                       | Judge     | OpenAI API (paid) | Stronger than the app model; works with RAGAS and DeepEval unchanged                      | Yes         |           |
| `gpt-4.1`                      | Judge     | OpenAI API (paid) | Strong rubric following for custom judges                                                 | Alt         |           |
| OpenRouter (`OPENAI_BASE_URL`) | Gateway   | Paid API          | Same code, other providers' models as a second judge; the repo README documents the setup |             |           |

**Your suggestion:**

## Stage 3 — Embeddings and vector store

The retrieval layer the RAG metrics will judge. Pick a store that runs in-process, so the
tutorial needs no server. Embeddings come from the OpenAI API, so no model is downloaded.

| Option                     | Role         | Licence           | What it gives the tutorial                                                                         | Recommended | Your pick |
| -------------------------- | ------------ | ----------------- | -------------------------------------------------------------------------------------------------- | ----------- | --------- |
| `text-embedding-3-small` | Embeddings   | OpenAI API (paid) | Course 03 already uses it; cheap enough to re-embed the whole knowledge base                       | Yes         |           |
| `text-embedding-3-large` | Embeddings   | OpenAI API (paid) | Higher retrieval quality at about 6x the cost; useful for a "does the embedder matter?" comparison | Alt         |           |
| Chroma                     | Vector store | Apache 2.0        | In-process, persists to disk; course 03 already uses it                                            | Yes         |           |
| Qdrant                     | Vector store | Apache 2.0        | Local mode or server; strong metadata filtering                                                    |             |           |
| FAISS                      | Index        | MIT               | Raw speed, no metadata; good for retrieval-only drills                                             |             |           |
| LanceDB                    | Vector store | Apache 2.0        | Embedded, columnar; versions the table                                                             |             |           |

**Your suggestion:**

## Stage 4 — Golden set and test-set generation

The cases and expected answers every later stage scores against. Synthetic generators give
volume fast; a hand-written, stratified core gives the cases a release decision can trust.

| Option                                          | Licence    | What it gives the tutorial                                                                        | Recommended | Your pick |
| ----------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------- | ----------- | --------- |
| Hand-written stratified set (JSON in `data/`) | —         | Labelled by slice (easy, multi-hop, out-of-scope, adversarial); the method course 03 teaches      | Yes         |           |
| RAGAS testset generator                         | Apache 2.0 | Builds question–context–answer triples from the knowledge base via a knowledge graph            | Yes         |           |
| DeepEval Synthesizer                            | Apache 2.0 | Generates goldens from documents, with evolution steps for harder variants                        | Alt         |           |
| Giskard RAGET                                   | Apache 2.0 | Generates questions by type (simple, complex, distracting, situational) and reports per component |             |           |

**Your suggestion:** *Use `Hand-written stratified set` and RAGAS testset generator*

## Stage 5 — Deterministic retrieval metrics

Recall@k, precision@k, MRR and nDCG against labelled chunk IDs. No model involved, so these run
free, in milliseconds, and give the same number every time.

| Option                | Licence    | What it gives the tutorial                                            | Recommended | Your pick |
| --------------------- | ---------- | --------------------------------------------------------------------- | ----------- | --------- |
| Plain Python (stdlib) | —         | Each metric written out in ~5 lines, so the learner sees the formula  | Yes         |           |
| `ranx`              | MIT        | Fast, tested implementations plus significance tests between two runs | Yes         |           |
| `pytrec_eval`       | MIT        | The TREC reference implementation; the number papers report           |             |           |
| BEIR                  | Apache 2.0 | Public retrieval benchmarks to compare against an outside baseline    |             |           |

**Your suggestion:**

## Stage 6 — LLM-judged RAG metrics

Faithfulness, answer relevancy, context precision and context recall: did the answer stay
inside the retrieved text, and was the right text retrieved? Each option below uses the OpenAI
judge model from Stage 2.

| Option               | Licence    | What it gives the tutorial                                                                              | Recommended | Your pick |
| -------------------- | ---------- | ------------------------------------------------------------------------------------------------------- | ----------- | --------- |
| RAGAS                | Apache 2.0 | The standard RAG metric set; 0.4 moved metrics to `ragas.metrics.collections` with async `ascore()` | Yes         |           |
| DeepEval RAG metrics | Apache 2.0 | Same ideas, with a written reason per score; pytest-style runner                                        | Yes         |           |
| TruLens              | MIT        | The "RAG triad" (context relevance, groundedness, answer relevance) with a local dashboard              |             |           |
| RAGChecker           | Apache 2.0 | Claim-level diagnosis that splits blame between retriever and generator                                 | Alt         |           |

**Your suggestion:**

## Stage 7 — Agent, tool-call and trajectory metrics

Right tool, right arguments, a sound path, and the goal met. Tool name and argument checks are
deterministic; path quality and goal completion need a judge.

| Option                               | Licence    | What it gives the tutorial                                                                      | Recommended | Your pick |
| ------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------- | ----------- | --------- |
| Deterministic checks in plain Python | —         | Exact match on tool name and arguments, order-aware trajectory comparison                       | Yes         |           |
| DeepEval agent metrics               | Apache 2.0 | Tool correctness, argument correctness, task completion over a trace                            | Yes         |           |
| RAGAS agent metrics                  | Apache 2.0 | Tool call accuracy and agent goal accuracy on multi-turn samples                                | Alt         |           |
| `agentevals` (LangChain)           | MIT        | Trajectory match modes (strict, unordered, subset) plus an LLM trajectory judge; fits LangGraph | Alt         |           |
| Inspect AI (UK AISI)                 | MIT        | Agent tasks run in Docker sandboxes with scorers; strongest for long, multi-step tasks          |             |           |

**Your suggestion:**

## Stage 8 — Tracing, experiments and datasets

Where runs are recorded, compared side by side, and turned back into test cases. Emitting traces
as OpenTelemetry keeps the choice reversible: any of these can read them.

| Option                      | Licence                        | What it gives the tutorial                                                                    | Recommended    | Your pick |
| --------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------- | -------------- | --------- |
| LangSmith | Proprietary (SDK MIT) | LangGraph traces automatically; datasets, `evaluate()` experiments, annotation queues, online evaluators. Free plan: 5k traces/month, 14-day retention, 1 seat | Yes (decided 2026-10-18) | Use |
| Langfuse                    | MIT (core)                     | Traces, datasets, experiments, prompt versions and LLM-judge evaluators in one UI | Optional track |           |
| Opik (Comet)                | Apache 2.0                     | Same scope as Langfuse, with built-in metrics and a pytest integration                        | Alt            |           |
| MLflow 3 GenAI              | Apache 2.0                     | Tracing, `mlflow.genai.evaluate()` and scorers; course 02 already teaches it                |                |           |
| OpenLLMetry / OpenInference | Apache 2.0                     | OpenTelemetry instrumentation for LangGraph and LLM calls; feeds any backend above            | Yes            |           |
| Arize Phoenix               | Elastic 2.0 (source-available) | Good local trace UI, but not an OSI open-source licence                                       | Skip if strict |           |

**Your suggestion: Skip Arize Phoenix. Use LangFuse, OTEL**

## Stage 9 — Safety and red-teaming

What must never happen: prompt injection through retrieved text, leaked PII, unsafe tool calls.
Attack generators find failures; the Stage 2 judge or OpenAI's moderation endpoint scores them.

| Option                                                  | Role          | Licence                 | What it gives the tutorial                                                                 | Recommended | Your pick |
| ------------------------------------------------------- | ------------- | ----------------------- | ------------------------------------------------------------------------------------------ | ----------- | --------- |
| DeepTeam                                                | Attacks       | Apache 2.0              | Red-team attacks and vulnerability scans from the DeepEval team; same test-case shape      | Yes         |           |
| garak (NVIDIA)                                          | Attacks       | Apache 2.0              | Probe library for jailbreaks, injection and leakage                                        | Alt         |           |
| PyRIT (Microsoft)                                       | Attacks       | MIT                     | Multi-turn attack orchestration with scoring                                               |             |           |
| Safety rubric on the Stage 2 judge (DeepEval `GEval`) | Scorer        | Apache 2.0 + OpenAI API | Policy-specific pass/fail (PII, unsafe tool call, off-policy answer) with a written reason | Yes         |           |
| OpenAI Moderation (`omni-moderation-latest`)          | Classifier    | OpenAI API (free)       | Generic harm categories at no cost; a baseline beside the custom rubric                    | Alt         |           |
| NeMo Guardrails                                         | Runtime rails | Apache 2.0              | Turns the checks into runtime blocks, for the "guardrail vs eval" lesson                   |             |           |

**Your suggestion: Use DeepTeam, and DeepEval GEval**

## Stage 10 — Human labels and judge calibration

A judge is trusted only after it agrees with people. Collect human pass/fail labels on a sample,
then report the judge's agreement (Cohen's kappa, true-positive and true-negative rates) before
using its scores.

| Option                                            | Licence    | What it gives the tutorial                                                      | Recommended | Your pick |
| ------------------------------------------------- | ---------- | ------------------------------------------------------------------------------- | ----------- | --------- |
| Notebook widget (ipywidgets) writing to `data/` | BSD-3      | Zero setup; the approach course 03 uses                                         | Yes         |           |
| LangSmith annotation queues | Proprietary | Labels attach to the run they judge; same platform as Stage 8 | Yes (decided 2026-10-18) | Use |
| Langfuse annotation queues                        | MIT (core) | Labels attach to the trace they judge; no second tool if Stage 8 picks Langfuse | Optional track |           |
| Argilla                                           | Apache 2.0 | Dedicated labelling UI with multiple annotators and agreement stats             | Alt         |           |
| Label Studio                                      | Apache 2.0 | General-purpose labelling; heavier to set up for text-only tasks                |             |           |

**Your suggestion: Use Notebook Widget and Langfuse Annotation Queue**

## Stage 11 — CI release gate

The step that says "don't ship": compare the candidate's scores per slice against thresholds and
the baseline, and fail the build on a regression. Scoring calls the paid OpenAI API, so it runs
in a manual job, never on every push or PR; the comparison job is free and runs on every change.

| Option                                              | Licence    | What it gives the tutorial                                                                                                   | Recommended | Your pick |
| --------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------- | --------- |
| Stdlib gate script + GitHub Actions                 | —         | Thresholds and confidence intervals in plain Python; course 03 notebook 11's design                                          | Yes         |           |
| `deepeval test run`                               | Apache 2.0 | pytest-style pass/fail per case, ready for CI                                                                                | Alt         |           |
| promptfoo                                           | MIT        | YAML test matrix with assertions; built-in red-team mode                                                                     |             |           |
| Paid `evaluate` job on `workflow_dispatch` only | —         | Scores the candidate with `OPENAI_API_KEY`; skips itself when the secret is unset (course 03's `release-gate.yml` split) | Yes         |           |

**Your suggestion: Use both the  Stdlib gate script + GitHub Actions and Paid `evaluate` job on `workflow_dispatch` only**

## Stage 12 — Online evaluation and monitoring

In production there is no answer key. Score sampled live traces with reference-free judges,
watch for drift, and feed failing traces back into the Stage 4 golden set.

| Option                                   | Licence               | What it gives the tutorial                                                           | Recommended | Your pick |
| ---------------------------------------- | --------------------- | ------------------------------------------------------------------------------------ | ----------- | --------- |
| Langfuse online evaluators               | MIT (core)            | LLM-judge rules that score a sample of incoming traces; failing ones go to a dataset | Optional track |           |
| LangSmith online evaluators | Proprietary | LLM-judge or code evaluators on a sampled share of production runs | Yes (decided 2026-10-18) | Use |
| Opik online rules                        | Apache 2.0            | The same pattern, if Stage 8 picks Opik                                              | Alt         |           |
| Evidently                                | Apache 2.0            | Drift reports and LLM descriptors over logged data; batch, not per trace             |             |           |
| Prometheus + Grafana (via OpenTelemetry) | Apache 2.0 / AGPL-3.0 | Latency, cost and score dashboards with alerts                                       |             |           |

**Your suggestion: use Langfuse online evaluators**

## Optional — External agent benchmarks

Public benchmarks answer a different question from Stages 4–12: how does this model compare with
others, not whether this app works. Use one at most, as a sidebar.

| Option                           | Licence       | What it gives the tutorial                                                      | Recommended | Your pick |
| -------------------------------- | ------------- | ------------------------------------------------------------------------------- | ----------- | --------- |
| τ-bench                         | MIT           | Tool-using customer-service tasks with a simulated user; pass^k for reliability | Yes         |           |
| BFCL (Berkeley Function Calling) | Apache 2.0    | Function-call accuracy across simple, parallel and multi-turn calls             | Alt         |           |
| AgentDojo                        | MIT           | Prompt-injection attacks against tool-using agents; pairs with Stage 9          |             |           |
| GAIA                             | Gated dataset | General assistant tasks; needs web tools and is costly to run                   |             |           |

**Your suggestion: Ignore this Optional Stage.** 

## Recommended stack

One pick per stage gives a tutorial built on open-source frameworks and OpenAI models only. It
needs `OPENAI_API_KEY` and no local model or GPU.

1. **App:** LangGraph supervisor with a RAG node and tools, on `gpt-4o-mini`
2. **Judge:** `gpt-4o`, a stronger model than the app
3. **Retrieval layer:** `text-embedding-3-small` embeddings in Chroma
4. **Golden set:** hand-written stratified core, topped up with RAGAS-generated cases
5. **Retrieval metrics:** plain Python first, then `ranx` for significance tests
6. **RAG metrics:** RAGAS and DeepEval side by side on the same cases
7. **Agent metrics:** deterministic tool and argument checks, plus DeepEval task completion
8. **Traces and experiments:** LangSmith (free Developer plan); Langfuse as a later optional track
9. **Safety:** DeepTeam attacks, scored by a `GEval` safety rubric on the judge
10. **Human labels:** LangSmith annotation queues, then judge agreement (kappa)
11. **Release gate:** free stdlib gate on every push; paid scoring job on `workflow_dispatch` only
12. **Online:** LangSmith online evaluators, failing traces fed back to the golden set

Licences above are from memory as of mid-2026 and are approximate; check each project's licence
file before publishing.

**Your suggestion:**
