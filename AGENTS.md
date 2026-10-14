# Repository Guidelines

## Project Structure & Module Organization

- `courses/`: numbered, sequential notebook tracks for RAG/tool evaluation, MLflow, and an agentic evaluation harness. Read each track’s `README.md` before editing.
- `labs/`: independent demonstrations and evaluation scripts; some have separate environments.
- `docs/`: reference guides and interactive HTML; `INDEX.md` catalogs the material.
- `site/`: static-site builder and CSS; generated `site/dist/` is ignored. Register new documents in `site/build.py` under `RENDER`, `COPY`, or `SKIP`.
- `shared/`: legacy provider helpers. `archive/`: superseded material; preserve its contents and manifest.

## Build, Test, and Development Commands

Use Python 3.12+. Root dependencies and optional extras are declared in `pyproject.toml`; Ruff and pytest belong to the `dev` extra. Check the existing environment before syncing dependencies; root synchronization can remove Databricks Connect. Preserve the `langgraph==1.2.11` pin and course-specific requirements.

Run these free checks from the repository root:

```bash
# Build without changing the project environment
uv run --no-project --with markdown==3.7 python3 site/build.py
python3 -m http.server -d site/dist 8000
python3 .github/scripts/check_index_coverage.py
python3 .github/scripts/check_drill_sync.py
python3 .claude/skills/link-check/scripts/check_links.py docs
```

The final three commands verify index coverage, question-bank/drill consistency, and relative links.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions and variables, and `UPPER_CASE` constants. Preserve numbered notebook filenames and existing Markdown headings. Ruff is available; no repository-wide formatter configuration is defined.

Clear notebook outputs and set execution counts to `null` before committing. Course 02 shares Python modules; course 03 keeps helpers inside notebooks and exchanges state through `data/` files, using standard-library statistics. Preserve these designs. Leave third-party Arize lab formatting intact.

## Testing Guidelines

There is no repository-wide test suite or coverage threshold. DeepEval batch scripts use pytest-style `test_*.py` names and may incur API charges; never run bare root `pytest`. Execute paid notebooks, apps, and evaluations only when explicitly requested. Course 03’s free gate runs with `python3 ci/apply_gate.py` from its directory and requires generated evaluation results.

## Commit & Pull Request Guidelines

Follow history’s scoped messages, such as `docs(concepts): clarify scoring` or `feat(site): add navigation`. Keep changes focused. PRs, when used, should explain the affected track, validation performed, linked issues when relevant, and screenshots for visual changes. Update indexes and relative links after moves.

## Security & Configuration

Keep credentials in `.env`, using `.env.example` as the template. Never commit secrets, model-run artifacts, or generated site output.
