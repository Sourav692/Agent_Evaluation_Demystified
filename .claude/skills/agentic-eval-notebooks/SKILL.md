---
name: agentic-eval-notebooks
description: Build or extend the open-source agentic evaluation notebook series - a LangGraph multi-agent support system with a RAG agent, evaluated with RAGAS/DeepEval, a release gate, human feedback, and online evaluation. Use when creating, continuing, or reviewing notebooks in this project.
---

# Agentic Evaluation Notebooks

Build a 12-notebook open-source teaching series. The subject is the **evaluation harness and
release gate**, not the agent. The agent exists only to be measured.

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

## System under test - "Lumen Cloud" support assistant

```
                    Customer message
                          |
                   +------v------+
                   |  Supervisor |  classifies intent, routes
                   +------+------+
     +---------------+----+----------+----------------+
 +---v------+ +------v----+ +--------v--+ +-----------v--+
 |Knowledge | |  Billing  | |  Account  | |  Escalation  |
 |agent(RAG)| |   agent   | |   agent   | |    agent     |
 +---+------+ +------+----+ +--------+--+ +-----------+--+
     |               |               |                |
 help-center    get_invoice     get_account     create_ticket
 docs (Chroma,  issue_refund*   change_plan*
 3 languages)                   reset_password
                * writes pause for human approval
                          |
               SQLite = the final state
   (accounts, invoices, refunds, tickets, approvals)
```

Canonical multi-step run: *"I was double charged, and what's your refund policy?"* ->
Supervisor -> Knowledge agent (cited policy) -> Billing agent (invoice lookup, refund request)
-> approval -> reply. Exercises RAG, tool calls, a handoff, an approval gate, and a DB state
change.

**Fault switches** (each notebook's "Break it" section uses these):

| Fault | Breaks |
|---|---|
| `dense_only_retrieval`, `empty_index`, `citation_drift`, `thin_hindi_docs` | RAG agent |
| `wrong_tool`, `bad_arguments`, `tool_returns_empty` | Tool layer |
| `wrong_route`, `lost_handoff_context` | Agent / handoff layer |
| `skip_approval` | Safety |
| `retry_loop`, `verbose_prompt` | Cost and efficiency |

## Repo layout

```
agentic-eval-notebooks/
|- 01_rag_agent.ipynb ... 12_online_and_loop.ipynb
|- data/     golden_set.json, fixtures/, chroma/, lumen.db,
|            baseline_report.json, human_labels.jsonl, gate_result.json
|- tests/test_release_gate.py
|- .github/workflows/release-gate.yml
|- requirements.txt   (pinned)
`- README.md          (reading order + concept map)
```

## The 12 notebooks

### 01 - Knowledge base and the RAG agent
~40 fictional help-center articles (refund policy, plans, security, how-tos) in English,
Spanish, Hindi - Hindi deliberately thin in one category. Chunking, embedding, Chroma.
RAG agent: retrieve -> cite -> or refuse when docs don't cover it. Wire the RAG faults.
**Produces:** `data/chroma/`, the RAG agent function.

### 02 - Tools, specialist agents and the supervisor graph
SQLite schema + seed data. Tools as `@tool` functions with the approval step for
`issue_refund` and `change_plan`. Billing/account/escalation agents, supervisor routing
prompt, LangGraph assembly. **Trajectory capture:** each run -> one dict with steps, agent
per step, tool name and arguments, tool result type (`ok`/`empty`/`unavailable`), handoff
payloads, tokens, cost, final DB state. DeepEval `@observe` so spans exist for later
component-level scoring. Record-and-replay fixtures (frozen fixtures made concrete).
Remaining fault switches. **Produces:** `data/lumen.db`, `data/fixtures/`.

### 03 - The golden set
Case anatomy: input, expected route, expected tool calls and arguments, expected path,
expected final DB state, expected answer or refusal, stratum tags. Strata: language
(en/es/hi), intent (billing/account/knowledge/multi-intent/escalation), RAG question type
(factual/multi-hop/absent/contradictory/adversarial), single vs. multi-turn. Minimum case
count per stratum; over-sample small segments. At least 1/5 of cases must have refusal or
escalation as correct behavior. Load as both a DeepEval `EvaluationDataset` (Goldens) and
a RAGAS dataset. Datasheet + version. **Produces:** `data/golden_set.json`.

### 04 - RAG agent evaluation (RAGAS)
Context precision, context recall, faithfulness, response relevancy. Citation accuracy and
refusal correctness as custom RAGAS rubric metrics. Report by question type and language,
never as one average. Break with `citation_drift`, `thin_hindi_docs`. Interview angle: a
suite with no "absent" cases trains you to ship an overconfident system.

### 05 - Tool-call evaluation (level 1)
DeepEval `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`. RAGAS `ToolCallAccuracy`
(strict vs. flexible order), `ToolCallF1`. Result handling: empty vs. unavailable - retry,
escalate, or say so honestly? Repeated-call detection. Break with `wrong_tool`,
`bad_arguments`, `tool_returns_empty`.

### 06 - Agent, handoff and end-to-end evaluation (levels 2 and 3)
**Agent:** routing accuracy per intent + confusion matrix (custom); confidence-threshold
sweep via shadow run; handoff integrity (did customer ID, issue, prior findings survive?);
role adherence; RAGAS `TopicAdherence`. **Trajectory:** four matching modes as short
functions - exact, in-order, any-order, contains-required; DeepEval `PlanAdherenceMetric`.
**End-to-end:** DeepEval `TaskCompletionMetric`, `StepEfficiencyMetric`; RAGAS
`AgentGoalAccuracy` (with and without reference); **final-state check against SQLite** -
was the refund written, exactly once, for the right amount (no framework does this).
Multi-turn conversation scoring. **Blame attribution** via DeepEval component-level span
scores: find the first level that failed; failure count per agent. Break with `wrong_route`,
`lost_handoff_context`, `retry_loop`.

### 07 - Safety and policy checks
Deterministic assertions as plain functions: never refund without approval, never cross
customers, never call another agent's tools, never put personal data in the reply. A
DeepEval `DAGMetric` for judgment-call policies. Why safety is per-case, never averaged,
and blocks absolutely. Why a flaky safety test is a safety problem. Break with `skip_approval`.

### 08 - Building custom judges
`GEval` for reply quality; `DAGMetric` for decision-tree scoring; RAGAS rubric metrics for
the same job, compared. Reference-based vs. reference-free judging, and why the latter
survives into production. Bias tests: position bias (swap answers - does the verdict flip?)
and same-model bias.

### 09 - Human feedback and judge calibration
Three distinct kinds: runtime approvals inside the agent; end-user feedback (thumbs) in
production; expert annotation of sampled runs. An `ipywidgets` labeling panel writing
`data/human_labels.jsonl` (offline, no accounts). The same loop with self-hosted Langfuse:
annotation queues, user-feedback scores on traces. Judge calibration: agreement rate and
Cohen's kappa computed by hand; what to do when agreement drifts. Using human labels to set
gate thresholds rather than guessing. Promoting labeled production failures into new
goldens. Evaluating the approval gate itself: decision time, queue depth, and the
rubber-stamp signal (approval rate near 100% with near-zero decision time).

### 10 - Stratified reporting and statistics (no pandas, no scipy)
Group DeepEval/RAGAS scores into per-stratum reports with plain dicts. Report each
dimension separately (language, agent, intent); do not cross-tabulate into empty cells.
Sample-size arithmetic n ~= 15.7 * p(1-p) / delta^2; why a small suite only detects large
changes. Paired comparison, McNemar's test, bootstrap CI - ~10 lines of stdlib each.
Minimum case count per stratum so a "15-point drop" isn't one case flipping.
**Produces:** `data/baseline_report.json`.

### 11 - The release gate and CI
One gate function over the framework scores, four checks:
1. **Safety** - any violation blocks, regardless of everything else
2. **Aggregate floor** - resolution rate and faithfulness, paired against baseline
3. **Per-stratum floor** - by language, intent and agent
4. **Cost ceiling** - cost per resolved conversation

Thresholds in a config dict at the top of the notebook. Four scenarios: clean release;
Hindi stratum collapsing while the average rises; a safety violation; a cost blowup from
`verbose_prompt`. `tests/test_release_gate.py` using DeepEval `assert_test`. GitHub Actions
workflow that fails the PR when the gate blocks. **Produces:** `data/gate_result.json`.

### 12 - Online evaluation, alerts and closing the loop
Simulate a day of production traffic across intents and languages. Which metrics survive
without reference answers (faithfulness, goal accuracy without reference, topic adherence)
and which stay offline-only. Safety assertions on 100% of traffic; judge sampling on 1-2%.
Alerts: cost at 3x trailing median, citation-free answer rate, tool-status mix shifting
toward empty, approval decision time, loop rate per agent. Incident drills: `empty_index`
and `retry_loop` - which alert fires first, which stays silent. Canary: new vs. old on the
same traffic, paired win rate, rollback decision. The loop: sampled traces -> notebook 09
for human labels -> notebook 03 for new goldens -> drift check. Ecosystem map vs. RAGAS,
DeepEval, Langfuse, MLflow, LangSmith.

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

## Build workflow

1. **Build one notebook at a time, in order.** Each depends on the `data/` outputs of earlier
   ones.
2. **Generate `.ipynb` programmatically** with `nbformat` (write a small build script, or
   author `py:percent` files and convert with jupytext) rather than hand-writing notebook JSON.
3. **Execute every notebook before declaring it done:**
   `jupyter nbconvert --to notebook --execute --inplace <nb>.ipynb`. A notebook that has not
   executed cleanly end-to-end is not finished.
4. **Verify framework APIs against the installed version** before writing metric code - check
   the package's own docs or `help()`, don't rely on remembered names.
5. **Keep outputs committed** for the teaching value, but ensure a fresh clone can re-run
   everything offline via the recorded fixtures.
6. After each notebook, report: what it teaches, what it produces in `data/`, and what the
   next notebook consumes.

## Defaults for open decisions

Unless the user says otherwise: **Apache-2.0** license; **Ollama** as the default local model
with a one-line switch to a hosted provider; **ipywidgets annotation plus an optional
self-hosted Langfuse section** in notebook 09; build **01-04 first** and check in before
continuing.
