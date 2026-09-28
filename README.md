# Agent Evaluation Demystified

Hands-on material for answering one question: **how do you know your RAG system or
agent is actually working?**

Not "does it return something" — whether retrieval reached the right chunk, whether the
generator stayed grounded in it, whether the agent picked the right tool with the right
arguments, whether the task actually completed, and whether any of that still holds in
production a month later.

Covered across 60 notebooks and three courses, using **DeepEval**, **RAGAS**,
**MLflow 3 GenAI** and **Arize Phoenix** — deliberately the same ideas in four
frameworks, so the concept survives the tool going out of fashion.

---

## Where to start

Six entry points, depending on what you want:

| I want to… | Go to | Shape |
|---|---|---|
| **Follow one path from basic to expert** | [`docs/study-guide/evaluation-roadmap.md`](docs/study-guide/evaluation-roadmap.md) | Ten levels across all three courses, each with an exit check — then what an OpenAI round pushes on, and the Databricks track as its own ladder |
| **Learn it in order, start to finish** | [`courses/01-rag-agent-tool-evaluation/`](courses/01-rag-agent-tool-evaluation/) | 15 notebooks, 6 modules: deterministic retrieval metrics → LLM-judged → generator → tool use → trajectory → CrewAI capstone |
| **Learn the production/MLOps side** | [`courses/02-databricks-mlflow-evals/`](courses/02-databricks-mlflow-evals/) | 11 notebooks: one agent built in Phase 1, then offline eval, custom judges, datasets from traces, regression gating, online monitoring, judge alignment |
| **Build the thing that says "don't ship"** | [`courses/03-agentic-eval-harness/`](courses/03-agentic-eval-harness/) | 12 notebooks: one multi-agent system, a stratified golden set, then RAG → tool → agent → safety → judges → human labels → statistics → **a release gate wired to CI** → online eval |
| **Read, not run** | [`docs/`](docs/) | Three theory companions, six interactive HTML labs, one question bank — nothing to execute |
| **Prep for an eval-heavy interview** | [`docs/interview-prep/`](docs/interview-prep/) | A 54-item self-quiz drill, plus a staged study plan in [`docs/study-guide/`](docs/study-guide/) — standalone HTML, open the file, no setup |

**If you only have an hour:** course 01, modules 0 → 1.2 → 2.2 → 3.

**Prefer a browser?** Everything under `docs/` is published at
**[eval-demystified.vercel.app](https://eval-demystified.vercel.app)** — the theory companions,
the question bank, the roadmap, the drill, the study plan and all six interactive labs, with
navigation. Same content as the files here; the Markdown in `docs/` is canonical.

**Looking for one specific thing?** [`INDEX.md`](INDEX.md) is the lookup table — every
document, what each section covers, and a find-it-by-topic index down to the section number.

---

## Repository map

```
courses/     Finished, sequential. Start here.
  01-rag-agent-tool-evaluation/   RAG, tool-use and trajectory evaluation (15 notebooks)
  02-databricks-mlflow-evals/     MLflow 3 GenAI, offline → online (11 notebooks + 10 modules)
  03-agentic-eval-harness/        The harness and the release gate: RAGAS + DeepEval over a
                                  LangGraph multi-agent system, stratified reporting, CI
                                  (12 notebooks, complete)

labs/        Raw source material. Runnable, but not a curriculum — reach for these
             when a course points at one, or when you want the unabridged version.
  rag-evaluation/                 DeepEval metric drills, RAGAS scripts, a FastAPI RAG bot
  agent-evaluation/
    arize-phoenix-labs/           DeepLearning.AI × Arize: 5 progressive tracing/eval labs
    crewai-travel-planner/        A real 3-agent CrewAI app used as an evaluation target
    multi-agent-eval-demo/        Tiny LangGraph supervisor team + scorecard, behind FastAPI/Streamlit
  langgraph-agent-rag-eval/       Interview-prep notebooks: 9-metric trace-level suite
  multiturn-and-tool-eval/        Multi-turn + tool metrics, DeepEval vs MLflow side by side
  llm-as-judge/                   G-Eval smoke test

docs/        Prose only. Nothing executes. See INDEX.md for a section-level lookup.
  concepts/                       One theory companion per course, plus online vs. offline
  interactive-labs/               6 standalone HTML labs
  interview-prep/                 One question bank (35 questions + 25 metric questions
                                  + 19 cases), plus a self-quiz drill as standalone HTML
  study-guide/                    The staged study plan through that question bank,
                                  as standalone HTML

shared/      Small LLM/embedding provider helpers (OpenAI, Groq, Databricks)
archive/     Superseded material, kept for reference — see archive/README.md
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
| `phoenix` | `uv pip install -e '.[phoenix]'` | `labs/agent-evaluation/arize-phoenix-labs/` (also needs `PHOENIX_COLLECTOR_ENDPOINT`) |
| `crewai` | `uv pip install -e '.[crewai]'` | `labs/agent-evaluation/crewai-travel-planner/` (also needs `SERPER_API_KEY`) |
| `databricks` | `uv pip install -e '.[databricks]'` | `courses/02` phases 6–8 against a real workspace — phases 0–5 and 9–10 run locally on SQLite |
| `apps` | `uv pip install -e '.[apps]'` | the Streamlit demos in `labs/rag-evaluation/` |
| `agentic-eval` | `uv pip install -e '.[agentic-eval]'` | `courses/03-agentic-eval-harness/` — Chroma, ipywidgets |

`labs/multiturn-and-tool-eval/` has its own `uv` project and lockfile — run `uv sync`
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

## Provenance

This repository was split out of the larger `AI-ENGINEERING-DEMYSTIFIED` monorepo. A few
prose references still name files that stayed behind there (`NOTEBOOK_INDEX.md`, the
OpenAI coverage-gap analysis, the red-teaming notebook under
`12_Production_and_Observability/`). They are mentions, not links — nothing in this repo
depends on them.

`labs/agent-evaluation/arize-phoenix-labs/` is course material from DeepLearning.AI and
Arize, kept whole and substantially unmodified.
