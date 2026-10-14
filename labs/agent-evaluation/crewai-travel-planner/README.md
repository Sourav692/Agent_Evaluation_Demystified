# CrewAI travel planner — an app to evaluate

**Unique:** a real, running 3-agent CrewAI app, used as the system under test by
[`courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb`](../../../courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb).
The capstone notebook is the lesson; this folder is the target it scores.

| File | What it is |
|---|---|
| `TripCrew.py` | Three agents (interest search, local expert, travel concierge) on `gpt-4o-mini` |
| `tasks.py` | What each agent is asked to produce |
| `tools/` | `search_internet` (Serper web search) and `calculate` |
| `api_server.py` | FastAPI backend: `POST /plan_trip/` on `localhost:8000` |
| `main.py` | Streamlit front end that calls the backend |
| `evaluate_endtoend_test.py` | DeepEval `TaskCompletionMetric` over every row of `trip_questions.xlsx` |

## Run it

Every step below makes paid calls (OpenAI and Serper). Don't run it unless you mean to spend credits.

```bash
# In this folder, with OPENAI_API_KEY and SERPER_API_KEY in the repo's .env
uv pip install -e '../../..[crewai]'      # or the pip line in the capstone notebook
python api_server.py                       # terminal 1: the backend
deepeval test run evaluate_endtoend_test.py   # terminal 2: the evaluation
streamlit run main.py                      # optional: the UI
```

**Known quirk, kept on purpose:** the server route is `/plan_trip/` (trailing slash) but
`evaluate_endtoend_test.py` posts to `/plan_trip`. The capstone notebook explains why it is left
as is.
