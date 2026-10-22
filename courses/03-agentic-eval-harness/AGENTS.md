# Course 03 — conventions for editing these notebooks

The 12-notebook series is complete (see `README.md`). Follow these rules when you fix, extend
or re-run any notebook in this folder. They came from the `agentic-eval-notebooks` skill that
built the series.

## Non-negotiable conventions

1. **All logic lives inside the notebook.** No importable package, no `src/`, no shared
   modules. If two notebooks need the same helper, each defines it again.
2. **Notebooks hand off through files in `data/`**, never through imports.
3. **Simple, educational Python.** Dicts, lists, plain functions, `for` loops. No pydantic,
   no classes where a function works, no decorators beyond framework-required ones, no dense
   comprehensions, no heavy typing.
4. **Do not use pandas, numpy, scipy or matplotlib.** Metrics come from RAGAS/DeepEval;
   grouping uses plain dicts and `collections.defaultdict`; statistics use stdlib `statistics`
   and `random`; output uses the frameworks' own tables.
5. **Pin exact versions** in each notebook's first cell. RAGAS and DeepEval rename things
   between releases - verify current API names against the installed version before writing
   metric code, and never trust remembered API shapes.
6. **Every notebook follows the teaching template** (below), no exceptions.
7. **Deterministic by default.** Record-and-replay LLM fixtures mean notebooks and CI run
   with no API key.

## Teaching template (every notebook)

```
1. What you'll learn          - 3-4 bullets, markdown
2. The concept                - short markdown explanation + ASCII diagram
3. Build it                   - small code cells, one step each, plain-English comments
4. See it work                - run against the system under test
5. Break it                   - flip a fault switch, watch the metric or gate catch it
6. Try it yourself            - 1-2 exercises
7. Recap + interview angle    - how to explain this in a system design interview
```

## Tech stack

**Agent:** LangGraph - LangChain chat models (OpenAI/Anthropic/Ollama switchable) - Chroma -
sentence-transformers multilingual MiniLM - SQLite (stdlib) - `@tool` functions -
record-and-replay JSON fixtures.

**Evaluation:** RAGAS (RAG metrics) - DeepEval (tool/agent/end-to-end metrics, `@observe`
tracing, `GEval`, `DAGMetric`, pytest `assert_test`) - ipywidgets + self-hosted Langfuse
(human feedback) - plain Python (strata, stats, gate) - GitHub Actions (CI).

## Key concepts the notebooks must convey correctly

- **A gate is a decision layer, not another metric.** Metrics measure; the gate applies
  thresholds with consequences, stratified, wired to something that can refuse a deploy.
- **Offline vs. online:** offline catches large, deterministic, safety-critical regressions
  cheaply; online catches small drift and anything the dataset never represented.
- **Online judging needs no reference answers:** self-consistency judging (answer vs. its own
  logged context), deterministic trajectory rules, paired canary comparison, and delayed
  human labels for calibration - not inline scoring.
- **Stratified reporting:** tag every case, compute metrics within each tag group, gate on the
  worst stratum rather than the mean.
- **Three levels of agentic evaluation:** tool call -> agent/handoff -> end-to-end run, and
  every end-to-end failure gets traced back to the level that caused it.
