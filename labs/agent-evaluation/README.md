# Agent Evaluation

Evaluating agent *behaviour* — task success, routing, trajectories — rather than agent
building. Two independent bodies of material.

| Path | What it is | Needs |
|---|---|---|
| [`crewai-travel-planner/`](crewai-travel-planner/) | A real 3-agent CrewAI travel planner behind FastAPI, with a pytest `TaskCompletionMetric` suite that reads cases from `trip_questions.xlsx` and scores the live backend | `pip install -e '.[crewai]'`, `SERPER_API_KEY`, and the API server running |
| [`multi-agent-eval-demo/`](multi-agent-eval-demo/) | The smallest end-to-end version of the idea: a LangGraph supervisor routing between two specialists, a 4-case dataset recording which agents should work and what the answer must mention, three checkable scores (routing, content, efficiency) plus an LLM-judge quality score, served by FastAPI with a Streamlit scorecard. Moved here from `AI-ENGINEERING-DEMYSTIFIED` 2026-09-28 | `uv pip install -r multi-agent-eval-demo/requirements.txt`, `OPENAI_API_KEY` |

**Used by:** course 01 module 5
([`../../courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb`](../../courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb)),
an annotated walkthrough of the CrewAI eval script; the runnable app is here. Phoenix tracing
and experiments are taught in course 01 module 4
([`13_Production_Grade_Agent_Eval_Overview.ipynb`](../../courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb)).

## Notes

- **`crewai-travel-planner` is a live process**, not a notebook: start `api_server.py`,
  then run `evaluate_endtoend_test.py` against it.
