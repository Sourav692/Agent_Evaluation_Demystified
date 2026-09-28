# Agent Evaluation

Evaluating agent *behaviour* — task success, routing, trajectories — rather than agent
building. Three independent bodies of material.

| Path | What it is | Needs |
|---|---|---|
| [`arize-phoenix-labs/`](arize-phoenix-labs/) | The DeepLearning.AI × Arize course, kept whole as 5 progressive labs: build the agent under test → instrument it with Phoenix tracing → router & skill LLM-judge evals → trajectory evals via Phoenix experiments → structured evals comparing prompt versions | `pip install -e '.[phoenix]'` and `PHOENIX_COLLECTOR_ENDPOINT` in `.env` |
| [`crewai-travel-planner/`](crewai-travel-planner/) | A real 3-agent CrewAI travel planner behind FastAPI, with a pytest `TaskCompletionMetric` suite that reads cases from `trip_questions.xlsx` and scores the live backend | `pip install -e '.[crewai]'`, `SERPER_API_KEY`, and the API server running |
| [`multi-agent-eval-demo/`](multi-agent-eval-demo/) | The smallest end-to-end version of the idea: a LangGraph supervisor routing between two specialists, a 4-case dataset recording which agents should work and what the answer must mention, three checkable scores (routing, content, efficiency) plus an LLM-judge quality score, served by FastAPI with a Streamlit scorecard. Moved here from `AI-ENGINEERING-DEMYSTIFIED` 2026-09-28 | `uv pip install -r multi-agent-eval-demo/requirements.txt`, `OPENAI_API_KEY` |

**Distilled into:** course 01 modules 4 and 5
([`../../courses/01-rag-agent-tool-evaluation/`](../../courses/01-rag-agent-tool-evaluation/)).
Both are bridged rather than rebuilt there — module 4 is a concept map that links to these
labs in place, module 5 is an annotated walkthrough of the CrewAI eval script. The
runnable versions are here.

## Notes

- **The Arize labs share one `data/` and `images/` directory** at `arize-phoenix-labs/`,
  not one per lab. Notebooks reference them as `../data/` and `../images/`, so run each
  notebook with its own lab folder as the working directory.
- `helper.py`'s `get_phoenix_endpoint()` reads `PHOENIX_COLLECTOR_ENDPOINT` from `.env`,
  so the labs work against a self-hosted Phoenix instance — they are not tied to
  DeepLearning.AI's original hosted sandbox.
- **`crewai-travel-planner` is a live process**, not a notebook: start `api_server.py`,
  then run `evaluate_endtoend_test.py` against it.
