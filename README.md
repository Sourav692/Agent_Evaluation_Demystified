# Agent Evaluation Demystified

Hands-on material for answering one question: **how do you know your RAG system or
agent is actually working?**

Not "does it return something" — whether retrieval reached the right chunk, whether the
generator stayed grounded in it, whether the agent picked the right tool with the right
arguments, whether the task actually completed, and whether any of that still holds in
production a month later.

Covered across 43 notebooks — 38 in three courses, 5 in `labs/` — using **DeepEval**, **RAGAS**,
**MLflow 3 GenAI** and **Arize Phoenix** — deliberately the same ideas in four
frameworks, so the concept survives the tool going out of fashion.

---

## Where to start

**Two routes.** The **[Core path](courses/README.md#core-path)** is 21 notebooks, course 01 then
course 03. The **[Full path](docs/study-guide/evaluation-roadmap.md)** is the roadmap: every level, with
its Core and Optional notebooks.

Six entry points, depending on what you want:

| I want to… | Go to | Shape |
|---|---|---|
| **Follow one path from basic to expert** | [`docs/study-guide/evaluation-roadmap.md`](docs/study-guide/evaluation-roadmap.md) | Ten levels across all three courses, each with an exit check — then what an OpenAI round pushes on, and the Databricks track as its own ladder |
| **Learn it in order, start to finish** | [`courses/01-rag-agent-tool-evaluation/`](courses/01-rag-agent-tool-evaluation/) | 15 notebooks, 6 modules: deterministic retrieval metrics → LLM-judged → generator → tool use → trajectory → CrewAI capstone |
| **Learn the production/MLOps side** *(optional)* | [`courses/02-databricks-mlflow-evals/`](courses/02-databricks-mlflow-evals/) | **Optional track.** 11 notebooks: one agent built in Phase 1, then offline eval, custom judges, datasets from traces, regression gating, online monitoring, judge alignment |
| **Build the thing that says "don't ship"** | [`courses/03-agentic-eval-harness/`](courses/03-agentic-eval-harness/) | 12 notebooks: one multi-agent system, a stratified golden set, then RAG → tool → agent → safety → judges → human labels → statistics → **a release gate wired to CI** → online eval |
| **Read, not run** | [`docs/`](docs/) | Eleven roadmap explainers, two theory companions, a support-system case study with its cost companion, six interactive HTML labs, one question bank — nothing to execute |
| **Prep for an eval-heavy interview** | [`docs/interview-prep/`](docs/interview-prep/) | A 54-item self-quiz drill, plus a staged study plan in [`docs/study-guide/`](docs/study-guide/) — standalone HTML, open the file, no setup |

**If you only have an hour:** course 01 notebooks `00` → `02` → `09` → `12`.

**Prefer a browser?** Everything under `docs/` is published at
**[eval-demystified.vercel.app](https://eval-demystified.vercel.app)** — the theory companions,
the question bank, the roadmap, the drill, the study plan and all six interactive labs, with
navigation. Same content as the files here; the Markdown in `docs/` is canonical.

**Looking for one specific thing?** [`INDEX.md`](INDEX.md) is the lookup table — every
document, what each section covers, and a find-it-by-topic index down to the section number.

---

## Study roadmap

The whole subject in order, basic to expert. Each level is one explainer to read, its **Core**
notebooks to run, **Optional** notebooks that go deeper, and the question-bank sections to test
yourself on. Take the Core column alone for the short route (21 notebooks); take every column
for the Full path. The canonical version, with topics and exit checks per level, is
[`docs/study-guide/evaluation-roadmap.md`](docs/study-guide/evaluation-roadmap.md); notebook
codes are course/notebook (`c01/02` = course 01, notebook 02).

| # | Band | Level | The question it answers | Read | Core notebooks | Optional | Question bank | Time |
|---|---|---|---|---|---|---|---|---|
| 0 | Beginner | [Orientation](docs/study-guide/evaluation-roadmap.md#level-0-orientation) | What can be measured, and with what kind of scorer? | [Explainer 00](docs/roadmap-explainers/00-orientation.md) | [c01/00](courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) | — | Part 0 (§0.1–0.3) | 3 h |
| 1 | Beginner | [RAG](docs/study-guide/evaluation-roadmap.md#level-1-rag-retrieval-and-generation) | Did retrieval find it, and did the generator stay inside it? | [Explainer 01](docs/roadmap-explainers/01-rag-retrieval-and-generation.md) | [c01/01](courses/01-rag-agent-tool-evaluation/01_Retrieval_Metrics_Deterministic.ipynb), [c01/02](courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb), [c01/03](courses/01-rag-agent-tool-evaluation/03_Generator_Metrics_Referenceless.ipynb), [c01/04](courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb), [c03/04](courses/03-agentic-eval-harness/04_rag_evaluation_with_ragas.ipynb) | [c01/05](courses/01-rag-agent-tool-evaluation/05_RAG_Eval_Inside_the_Pipeline.ipynb), [c01/06](courses/01-rag-agent-tool-evaluation/06_RAGAS_in_Practice.ipynb), [c01/07](courses/01-rag-agent-tool-evaluation/07_RAG_Capstone_Build_and_Evaluate.ipynb) | Q5, Q8, §10.1–10.3 | 8 h |
| 2 | Intermediate | [Agents](docs/study-guide/evaluation-roadmap.md#level-2-agents-tools-conversations-trajectories-outcomes) | Right tool, right arguments, sound path, goal met? | [Explainer 02](docs/roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.md) | [c01/08](courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb), [c01/09](courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb), [c01/10](courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb), [c01/12](courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb), [c03/05](courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb) | [c01/11](courses/01-rag-agent-tool-evaluation/11_Same_Evals_with_MLflow.ipynb), [c01/14](courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb) | Part 7 (Q26–Q29), §10.4–10.5, Cases 7, 9 | 8 h |
| 3 | Intermediate | [Ground truth](docs/study-guide/evaluation-roadmap.md#level-3-ground-truth) | Where do the cases and the labels come from? | [Explainer 03](docs/roadmap-explainers/03-ground-truth.md) | [c03/01](courses/03-agentic-eval-harness/01_knowledge_base_and_rag_agent.ipynb), [c03/02](courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb), [c03/03](courses/03-agentic-eval-harness/03_the_golden_set.ipynb) | [c02/04](courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb) | Part 3 (Q10–Q13) | 4 h |
| 4 | Intermediate | [Judges](docs/study-guide/evaluation-roadmap.md#level-4-judges-and-the-humans-who-validate-them) | Why should anyone believe an LLM's score? | [Explainer 04](docs/roadmap-explainers/04-judges-and-the-humans-who-validate-them.md) | [c03/08](courses/03-agentic-eval-harness/08_building_custom_judges.ipynb), [c03/09](courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb) | [c02/03](courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb), [c02/07](courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb) | Part 4 (Q14–Q17), Cases 10–12 | 6 h |
| 5 | Advanced | [Statistics](docs/study-guide/evaluation-roadmap.md#level-5-statistics-and-stratified-reporting) | Is this change real, and for whom? | [Explainer 05](docs/roadmap-explainers/05-statistics-and-stratified-reporting.md) | [c03/10](courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb) | — | Q4, Q21 | 4 h |
| 6 | Advanced | [The gate](docs/study-guide/evaluation-roadmap.md#level-6-the-release-gate-and-ci) | Ship or don't ship — and who can loosen that? | [Explainer 06](docs/roadmap-explainers/06-the-release-gate-and-ci.md) | [c03/11](courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) | [c02/05](courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb), [c02/08](courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb) | Part 6 (Q22–Q25), Cases 13–14 | 5 h |
| 7 | Advanced | [Online](docs/study-guide/evaluation-roadmap.md#level-7-online-evaluation-and-the-loop) | What survives when the answer key is gone? | [Explainer 07](docs/roadmap-explainers/07-online-evaluation-and-the-loop.md) | [c03/12](courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb) | [c02/06](courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb), [c01/13](courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb) | Part 5 (Q18–Q20), Case 15 | 6 h |
| 8 | Expert | [Safety and multi-agent](docs/study-guide/evaluation-roadmap.md#level-8-safety-adversarial-and-multi-agent-attribution) | What must never happen, and which agent broke it? | [Explainer 08](docs/roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md) | [c03/06](courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb), [c03/07](courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) | [c02/09](courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb), [c02/10](courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb) | Part 8 (Q30–Q32), Cases 8, 16, 17 | 6 h |
| 9 | Expert | [The harness](docs/study-guide/evaluation-roadmap.md#level-9-the-harness-as-a-product) | How does the evaluation system stay trustworthy and affordable? | [Explainer 09](docs/roadmap-explainers/09-the-harness-as-a-product.md) | — [course 03 README](courses/03-agentic-eval-harness/README.md) | [c02/00](courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb) | Part 9 (Q33–Q35), Cases 18–19 | 4 h |
| 10 | Cram sheet | [The enterprise harness, end to end](docs/roadmap-explainers/10-the-enterprise-harness-end-to-end.md) | How do the ten levels fit into one harness? Nothing new — read it first for the shape, or last to get it back in one sitting | [Explainer 10](docs/roadmap-explainers/10-the-enterprise-harness-end-to-end.md) | — | — | — | 20 min |

Roughly 54 hours end to end. Alongside the levels:

| Track | What | Where |
|---|---|---|
| **Databricks / MLflow** *(optional)* | Course 02 phases 0–10 as its own ladder: tracing and scorers → datasets and gating → online evaluation and judge alignment → optimisation. Phases 6–8 need a workspace | [Roadmap, Databricks section](docs/study-guide/evaluation-roadmap.md#databricks--the-mlflow-3-genai-track-as-its-own-ladder) |
| **Interview prep** | 35 questions, 30 metric questions and 19 cases, plus a self-quiz drill and a staged study plan | [Question bank](docs/interview-prep/QUESTION_BANK.md) · [drill](docs/interview-prep/evaluation-round-drill.html) · [study plan](docs/study-guide/evaluation-study-plan.html) |
| **Templates** | Scorecard, failure investigation, acceptance criteria, regression report | [`evaluation-templates.md`](docs/study-guide/evaluation-templates.md) |
| **Short on time** | An hour, an evening, a weekend, two weeks — and interview tomorrow / 7 days / 30 days | [Roadmap, fast paths](docs/study-guide/evaluation-roadmap.md#fast-paths) |

---

## Repository map

| Folder | Role | Start at |
|---|---|---|
| [`courses/`](courses/) | **The curriculum.** Numbered, sequential, runnable notebooks | [`courses/README.md`](courses/README.md) — the Core path |
| [`docs/`](docs/) | **The theory.** Prose only, nothing executes; published as the website | [`docs/study-guide/evaluation-roadmap.md`](docs/study-guide/evaluation-roadmap.md) |
| [`labs/`](labs/) | What no course teaches, or a running app a course evaluates | [`labs/README.md`](labs/README.md) |
| [`archive/`](archive/) | Superseded material and retired labs. Every topic in it also lives above | [`archive/README.md`](archive/README.md) |
| [`site/`](site/) | Builds `docs/` into the website | [`site/README.md`](site/README.md) |
| [`shared/`](shared/) | Model-provider helpers. Intentionally unused — notebooks set up models inline | [`shared/README.md`](shared/README.md) |
| [`.github/`](.github/) | CI: three free docs gates, and course 03's release gate | — |

```text
Agent_Evaluation_Demystified/
├── courses/                              the curriculum, in order
│   ├── 01-rag-agent-tool-evaluation/     CORE · 15 notebooks: retrieval → generation →
│   │                                     multi-turn → tools → task completion → trajectory →
│   │                                     Phoenix tracing → CrewAI capstone
│   ├── 02-databricks-mlflow-evals/       OPTIONAL · 11 notebooks + 10 shared modules: the MLflow 3
│   │                                     loop on one agent; phases 6–8 need a Databricks workspace
│   └── 03-agentic-eval-harness/          CORE · 12 notebooks: golden set → RAG, tool and
│                                         agent evals → safety → judges → humans →
│                                         statistics → CI release gate → online
│                                         (own .venv, kernel, requirements.txt)
│
├── docs/                                 the theory — also the website
│   ├── study-guide/                      roadmap (the Full path), topic→notebook mapping,
│   │                                     evaluation templates, study plan (HTML)
│   ├── roadmap-explainers/               11 explainers, one per level (00–10)
│   ├── concepts/                         field guide (course 01), Databricks/MLflow
│   │                                     reference (course 02), support-system case
│   │                                     study, cost and guardrails
│   ├── interactive-labs/                 6 browser labs: move the numbers, watch the metrics react
│   ├── interview-prep/                   question bank (35 + 30 questions, 19 cases)
│   │                                     and a self-quiz drill
│   └── guide-audits/                     this repo against OpenAI's evaluation guide,
│                                         plus its plain-language tutorial
│
├── labs/                                 runnable extras a course points at
│   ├── agent-evaluation/
│   │   ├── crewai-travel-planner/        a live 3-agent CrewAI app — course 01 notebook 14's target
│   │   └── multi-agent-eval-demo/        a tiny supervisor team scored behind FastAPI/Streamlit
│   ├── langgraph-agent-rag-eval/         2 unabridged notebooks: the 9-metric trace-level suite
│   ├── rag-evaluation/                   a FastAPI RAG bot + the RAGAS pytest-CI pattern
│   │                                     (course 01 notebook 06)
│   └── rag-evaluation-techniques/        3 notebooks: GroUSE, Open-RAG-Eval, end-to-end RAGAS
│                                         (third-party, non-commercial licence)
│
├── archive/                              retired labs, earlier editions, merged docs — history only
├── site/                                 build.py renders docs/ into site/dist/ (gitignored)
├── shared/                               provider helpers (OpenAI, Groq, Databricks); not imported
├── .github/                              workflows/ (docs-sync, release-gate) and
│                                         scripts/ (the docs gates)
│
├── README.md                             you are here
├── INDEX.md                              section-level lookup: every document, find-by-topic
├── CLAUDE.md · AGENTS.md                 maintainer and coding-agent guidance
├── pyproject.toml · uv.lock              the root environment (requirements.txt mirrors it for pip)
├── vercel.json                           website build and redirects
├── .env.example                          every environment variable the code reads
└── LICENSE · LICENSE-docs · THIRD_PARTY.md
```

---

## Setup

Python 3.12+. [`uv`](https://docs.astral.sh/uv/) recommended.

```bash
git clone <this repo> && cd Agent_Evaluation_Demystified

uv sync                      # or: python -m venv .venv && pip install -e .
cp .env.example .env         # then fill in OPENAI_API_KEY
```

`OPENAI_API_KEY` alone runs most of the material. Everything else is per-track:

| Extra | Install | Needed by |
|---|---|---|
| `phoenix` | `uv pip install -e '.[phoenix]'` | `courses/01` notebook 13 — Phoenix tracing, evals and experiments (needs a running `phoenix serve`; set `PHOENIX_COLLECTOR_ENDPOINT` only if it is not on `localhost:6006`) |
| `crewai` | `uv pip install -e '.[crewai]'` | `labs/agent-evaluation/crewai-travel-planner/` (also needs `SERPER_API_KEY`) |
| `databricks` | `uv pip install -e '.[databricks]'` | `courses/02` phases 6–8 against a real workspace — phases 0–5 and 9–10 run locally on SQLite |
| `apps` | `uv pip install -e '.[apps]'` | the Streamlit demos in `labs/rag-evaluation/` |
| `agentic-eval` | `uv pip install -e '.[agentic-eval]'` | `courses/03-agentic-eval-harness/` — Chroma, ipywidgets |

To route OpenAI calls through OpenRouter or another OpenAI-compatible gateway, also set `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
(the openai SDK reads it; no repo code does) and use provider-prefixed model names such as `openai/gpt-4o-2024-08-06`.

`archive/labs-multiturn-and-tool-eval/` has its own `uv` project and lockfile — run `uv sync`
inside that directory rather than using the root environment.

`courses/03-agentic-eval-harness/` also carries its own `requirements.txt` with **exact**
pins, because notebooks 04–06 are written against specific RAGAS and DeepEval releases that
renamed things. The `agentic-eval` extra above is the loose-pinned equivalent; prefer the
course's own file if a metric import fails.

> **One pin worth knowing about.** `langgraph` is pinned to `1.2.11`. Installing `ragas`
> or `mlflow` can resolve it back to `1.0.x`, which drops `langgraph.runtime.ExecutionInfo`
> and silently breaks every LangGraph notebook here. If a resolver downgrades it, re-pin it.

---

## The website

[`site/build.py`](site/) renders the Markdown under `docs/` and copies the standalone HTML pages
into `site/dist/`, which is what **https://eval-demystified.vercel.app** serves.

| | |
|---|---|
| Hosting | Vercel project `eval-demystified` (team `sourav-dbx`), Git-connected to this repo, production branch `main` |
| Deploy | **Push to `main`.** Vercel runs the build command in [`vercel.json`](vercel.json) — a venv, `pip install -r site/requirements.txt`, `python3 site/build.py` — and serves `site/dist/`. No manual publish step |
| Local preview | `pip install -r site/requirements.txt && python3 site/build.py && python3 -m http.server -d site/dist 8000` |
| Adding a page | Register it in `RENDER`, `COPY` or `SKIP` in `site/build.py` — the build refuses a file in none of the three. See [`site/README.md`](site/README.md) |

`site/dist/` is a build artifact and is gitignored, like `mlruns/`. The three checks in
[`.github/workflows/docs-sync.yml`](.github/workflows/docs-sync.yml) run on every push that
touches `docs/`; they are free and catch the index, link and drill drift that would otherwise
ship.

## Conventions

- **Notebooks are numbered where order matters** (`courses/`) and not where it doesn't (`labs/`).
- **Directories** are `lowercase-kebab-case`. Notebook filenames inside the courses keep
  their original `NN_Title_Case.ipynb` form — they cross-reference each other by name.
- **Never commit `.env`.** `.env.example` lists every variable the code reads.
- **Run artifacts are gitignored** — `mlruns/`, `mlflow.db`, `.deepeval/`, persisted Chroma
  stores. Re-running the notebook regenerates them.

---

## Licence

Code is [MIT](LICENSE). Written material — `docs/` and the notebooks' prose — is
[CC BY 4.0](LICENSE-docs). Third-party folders keep their own terms: see
[`THIRD_PARTY.md`](THIRD_PARTY.md).

## Provenance

This repository was split out of the larger `AI-ENGINEERING-DEMYSTIFIED` monorepo. A few
prose references still name files that stayed behind there (`NOTEBOOK_INDEX.md`, the
OpenAI coverage-gap analysis, the red-teaming notebook under
`12_Production_and_Observability/`). They are mentions, not links — nothing in this repo
depends on them.

`labs/rag-evaluation-techniques/` is from Nir Diamant's *RAG_Techniques* anthology and keeps
its own non-commercial licence. Earlier drafts and superseded labs are in `archive/`, listed in
`archive/README.md`.
