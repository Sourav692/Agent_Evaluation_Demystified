# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Setup, the repo map and the per-track API keys are in @README.md — read it rather than re-deriving them.

## Never run anything that costs money without asking

Almost every file here calls a live OpenAI/judge model. **Do not execute notebooks, eval
scripts, or Streamlit apps unless explicitly asked.** Edit and reason about them statically.

The `test_*.py` files are **not a pytest suite** — they are DeepEval batch scripts that use
pytest only as a runner, and they make paid API calls. There is no repo-wide test suite.
Never run bare `pytest` at the root; it would sweep all of them up and spend credits.

| File | What it actually is |
|---|---|
| `labs/multiturn-and-tool-eval/test_*.py` | DeepEval metric drills (`deepeval test run <file>`) |
| `labs/llm-as-judge/DeepEval_GEval/test_firstdeepeval.py` | G-Eval smoke test |
| `labs/agent-evaluation/crewai-travel-planner/evaluate_endtoend_test.py` | Needs a running FastAPI server first |
| `courses/03-agentic-eval-harness/tests/test_release_gate.py` | LLM-driven release-gate drill (`deepeval test run <file>`). Skips itself unless `data/candidate_runs.json` exists |

**There is now one CI workflow**, `.github/workflows/release-gate.yml`, scoped by a `paths:`
filter to `courses/03-agentic-eval-harness/**`. It is inert for the rest of the repo. Its
`gate` job is free and standard-library-only; its `evaluate` job is the paid one and runs on
`workflow_dispatch` only, skipping itself when no `OPENAI_API_KEY` secret is set. Do not move
the paid job onto the push/PR path — the split is the subject of that course's notebook 11.

## The langgraph pin is load-bearing

`langgraph` is pinned to `==1.2.11` in `pyproject.toml` and `requirements.txt`. Installing or
resolving `ragas` or `mlflow` can silently pull it back to `1.0.x`, which drops
`langgraph.runtime.ExecutionInfo` and breaks every LangGraph notebook. If a resolver
downgrades it, re-pin it — do not "fix" the pin by floating it.

## Folder contract

Set by the restructure; each folder has a `README.md` acting as its index.

- **`courses/`** — finished and sequential. Notebooks are numbered, and later ones assume state
  from earlier ones. `courses/02-databricks-mlflow-evals/` notebooks additionally share mutable
  modules (`agent.py`, `scorers.py`, `promotion.py`, …) and reuse names defined in Phase 0
  (`AGENT_SPEC`, `EVAL_DIMENSIONS`, `QUALITY_GATES`) — they are order-dependent.
  `courses/03-agentic-eval-harness/` deliberately inverts that: **no shared modules, ever**.
  Helpers are redefined in each notebook and state is handed off through files in `data/`, so
  any notebook can be opened alone. Do not "fix" the duplication by extracting a module. It
  also bans pandas, numpy, scipy and matplotlib — grouping is `defaultdict`, statistics are
  stdlib. All 12 notebooks are written.
- **`labs/`** — raw source material, deliberately unnumbered because order doesn't matter.
- **`docs/`** — prose only. Nothing in here executes.
- **`archive/`** — superseded material. **Never delete from it**; `archive/README.md` is a
  manifest explaining why each file is there.

Course notebooks **cross-reference each other by filename**, and folder READMEs link across
directories with relative paths. Moving or renaming any file requires sweeping those links —
commits `2faa463` and `ac8c306` exist solely to repair breakage from skipping that step.

## Don't touch

- `labs/agent-evaluation/arize-phoenix-labs/` is third-party DeepLearning.AI × Arize course
  material, kept whole and substantially unmodified. Do not reformat or restyle it.
- `shared/` is **intentional dead code** — nothing imports it, because notebooks initialise
  models inline to stay copy-pasteable. `shared/utils.py` unconditionally imports
  `databricks_langchain` and `langchain_groq`, so it fails to import without those extras.

## Environments

**There is no working root environment right now.** The root `.venv` is a **Databricks Connect**
env — about 66 packages (`databricks-connect`, `databricks-sdk`, `ipykernel`, `pandas`,
`pyarrow`), built alongside the untracked `databricks.yml`. None of the `pyproject.toml`
dependencies are installed in it and there is no `uv.lock`. A `ModuleNotFoundError` from a
`courses/` or `labs/` notebook running on the `python3` kernel is usually this, not a genuinely
missing package. `pyproject.toml` still describes the *intended* root env for `courses/01`,
`courses/02` and most of `labs/` — treat it as a spec, not as the installed state.

**Ask before running `uv sync` at the root.** With no lockfile it resolves fresh and **prunes
`databricks-connect`**, which is not in `pyproject.toml` (the `databricks` extra lists only
`databricks-langchain` and `databricks-sdk`). That silently undoes the Databricks Connect setup.

`VIRTUAL_ENV` points at the root `.venv`, so a bare `uv pip install` targets it **even when run
from inside another folder that has its own `.venv`**. Always pass `--python <venv>/bin/python`.

Two folders have their own environment and their own kernel — don't mix either with the root:

| Folder | Environment | Kernel |
|---|---|---|
| `labs/multiturn-and-tool-eval/` | separate uv project + lockfile, older `deepeval==3.8.8` — `uv sync` inside it | its own |
| `courses/03-agentic-eval-harness/` | own `.venv` + `requirements.txt` — `uv pip install --python .venv/bin/python -r requirements.txt` | `agentic-eval-harness` |

Course 03's pins are **exact** (`deepeval==4.2.3`, `ragas==0.4.3`, `chromadb`, and
`ipykernel==6.30.1` — 7.x deadlocks nbclient part way through an `--execute` run), and its
notebooks 04–06 are written against those exact releases:
RAGAS 0.4 moved metrics to `ragas.metrics.collections` with an async `ascore()`, and DeepEval
4.x replaced `LLMTestCaseParams` with `SingleTurnParams` in `GEval`. Verify metric imports
against the installed version before editing that course's metric code — remembered API shapes are wrong
here more often than not.

Those pins are a system, not a list, and three of them only conflict at install time: `chromadb`
<=1.5.2 caps `posthog<6.0.0` while DeepEval 4.x needs `posthog>=7.0.0`; `ragas==0.4.3` pulls
`instructor`, which caps `openai<3.0.0`; and `ragas==0.4.3` hard-imports
`langchain_community.chat_models.vertexai`, which **`langchain-community` 0.4.2 deleted** — so
it is held at `0.3.31`. Note that `0.4.1` still ships a working copy of that module and `import
ragas` succeeds there, so `0.4.1` is an equally valid pin; `0.3.31` is the conservative choice,
not the only one. What must not happen is an unpinned resolve, which takes 0.4.2+ and breaks
`import ragas` outright. Either pin keeps the rest of the stack current: `0.3.31` asks for
`langchain-core<2.0,>=0.3.78`, which `1.6.2` satisfies, and `langgraph` stays at `1.2.11`. The reasons are commented in that
`requirements.txt` — re-check all three before moving any one of them.

`courses/02` phases 0–5 and 9–10 run locally against `sqlite:///mlflow.db`. That must be a DB
backend, not a `file://` store — the MLflow Prompt Registry requires it. Phases 6–8 need a real
Databricks workspace.

## Notebooks

Follow the formatting contract in @.claude/skills/format-notebook/SKILL.md when creating or
editing notebooks — heading structure, `# ====` section banners, import order, emoji conventions.

**Clear all outputs and reset `execution_count` to null before committing a notebook.** A git
`pre-commit` hook enforces this, but produce clean notebooks rather than relying on it.

## Git

Solo repo: commit straight to `main` when asked, no branch or PR ceremony. There is no `gh` CLI
installed. Never commit `.env` — `.env.example` lists every variable the code reads.
