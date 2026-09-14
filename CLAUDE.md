# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Setup, the repo map and the per-track API keys are in @README.md — read it rather than re-deriving them.

## Never run anything that costs money without asking

Almost every file here calls a live OpenAI/judge model. **Do not execute notebooks, eval
scripts, or Streamlit apps unless explicitly asked.** Edit and reason about them statically.

The `test_*.py` files are **not a pytest suite** — they are DeepEval batch scripts that use
pytest only as a runner, and they make paid API calls. There is no repo-wide test suite and
no CI. Never run bare `pytest` at the root; it would sweep all of them up and spend credits.

| File | What it actually is |
|---|---|
| `labs/multiturn-and-tool-eval/test_*.py` | DeepEval metric drills (`deepeval test run <file>`) |
| `labs/llm-as-judge/DeepEval_GEval/test_firstdeepeval.py` | G-Eval smoke test |
| `labs/agent-evaluation/crewai-travel-planner/evaluate_endtoend_test.py` | Needs a running FastAPI server first |

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

Root env covers `courses/` and most of `labs/` (`uv sync`). `labs/multiturn-and-tool-eval/` is a
**separate uv project** with its own lockfile pinning an older `deepeval==3.8.8` — run `uv sync`
inside that directory and use its own kernel, don't mix it with the root environment.

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
