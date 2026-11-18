# Course 04 Guide: End-to-End Evaluation

One support assistant, evaluated from every angle. The course builds a support agent for
**Pinecrest Outdoor Supply**, a fictional outdoor-gear store. It writes a golden set for that
agent, then scores retrieval, answers, tool calls, paths, task completion, conversations and
safety. Notebooks 10–14 build custom judges, calibrate them against human labels, compare app
versions with statistics, gate the release in CI and score live traffic.

This guide covers the whole course in one place: what each notebook teaches, the files it reads
and writes, and where it stands today. For setup, see [`README.md`](README.md). For why each tool
was picked, see [`PLAN.md`](PLAN.md). Every metric's definition is in
[`EVALUATIONS.md`](EVALUATIONS.md), and [`TRACKER.md`](TRACKER.md) tracks the build task by task.

## At a glance

| # | Notebook | Module | Evaluations (§ in `EVALUATIONS.md`) | Writes | Status |
|---|---|---|---|---|---|
| 01 | [Knowledge base and RAG agent](01_knowledge_base_and_rag_agent.ipynb) | A. The app | None (builds the app) | `kb_chunks.json`, `chroma_db/` | Run |
| 02 | [Tools, agents and the supervisor graph](02_tools_agents_and_supervisor_graph.ipynb) | A. The app | None (builds the app) | `agent_runs.json` | Run |
| 03 | [The golden set](03_the_golden_set.ipynb) | B. Test data | §0 test case contract, §1 golden set quality | `golden_set.json` | Run |
| 04 | [Retrieval evaluation](04_retrieval_evaluation.ipynb) | C. RAG | §2 ranked retrieval, §3 judged retrieval | `golden_runs.json` | Run |
| 05 | [Generation evaluation](05_generation_evaluation.ipynb) | C. RAG | §4 reference-free, §5 reference-based, §6 blame | `rag_scores.json` | Run |
| 06 | [Tool-call evaluation](06_tool_call_evaluation.ipynb) | D. Agent | §7 tool calls | `agent_scores.json` | Run, outputs not saved |
| 07 | [Trajectories and handoffs](07_trajectories_and_handoffs.ipynb) | D. Agent | §8 trajectory, §9 routing and handoffs | `agent_scores.json` | Run |
| 08 | [Task completion and conversations](08_task_completion_and_conversations.ipynb) | D. Agent | §10 task completion, §11 multi-turn | `agent_scores.json`, `conversation_scores.json` | Run |
| 09 | [Safety and red-teaming](09_safety_and_red_teaming.ipynb) | E. Safety | §12 safety and adversarial | `safety_scores.json` | Run |
| 10 | [Custom judges](10_custom_judges.ipynb) | F. Judges | §13 custom judges | `custom_judge_scores.json` | Written, not run |
| 11 | Calibrating judges with human labels | F. Judges | §14 judge calibration | `judge_trust.json` | Planned |
| 12 | Statistics, cost and experiments | G. Decisions | §15 statistics, §16 cost and latency, §17 regression experiments | `baseline_scores.json`, `candidate_scores.json` | Planned |
| 13 | The release gate and CI | G. Decisions | §18 release gate | `gate_rules.json`, `gate.py`, a workflow | Planned |
| 14 | Online evaluation and the loop | H. Production | §19 online evaluation | Reviewed failures back into `data/` | Planned |

All file names in the Writes column live in `data/`.

## The system under test

The agent being evaluated is a LangGraph supervisor with three paths:

- **Router (supervisor):** a structured LLM decision that sends each message to one path.
- **RAG agent:** answers from 9 support articles (returns, refunds, shipping, warranty, orders,
  loyalty, product care, account and privacy, contact and escalation), split into 31 chunks with
  stable IDs and stored in Chroma.
- **Account agent:** a tool-calling loop over four tools (`lookup_order`, `issue_refund`,
  `create_ticket`, `search_kb`) against a mock order database. `issue_refund` enforces the business rules: matching email, return window,
  and a $500 limit.
- **Escalation:** hands the case to a human.

| Role | Model |
|---|---|
| App (the agent under test) | `deepseek/deepseek-v4-flash-0731` on OpenRouter (set in `models.toml`) |
| Judge | `qwen/qwen3-235b-a22b-2507` on OpenRouter (set in `models.toml`) |
| Embeddings | `openai/text-embedding-3-small` on OpenRouter |
| Simulated customers and attack writers | `openai/gpt-4o-mini` on OpenRouter |
| RAGAS test-set generator (cached) | `openai/gpt-4o` on OpenRouter |

Traces, datasets, experiments and human labels live in LangSmith (free Developer plan).

### The golden set

Every evaluation after notebook 03 runs on one set of 121 cases in six slices:

| Slice | Cases | What it tests |
|---|---|---|
| `simple` | 21 | A question one support article answers |
| `multi_hop` | 20 | A question that needs facts from more than one chunk |
| `out_of_scope` | 20 | A question the articles don't cover; the right answer is a decline |
| `tool_required` | 20 | A request the account agent must act on with a tool |
| `handoff` | 20 | A case the policy says must go to a human |
| `adversarial` | 20 | An attempt to make the agent break a rule |

Each case carries every label a later notebook needs: `input`, `reference_answer`,
`relevant_chunk_ids`, `expected_agent`, `expected_tool_calls`, `expected_end_state`, `policy_tags`
and `source` (hand-written or RAGAS-generated).

## How the course is built

- **Each notebook stands alone.** Open any notebook and run it top to bottom. Results pass between
  notebooks as files in `data/`. If an input file is missing, the notebook names the notebook that
  writes it.
- **No shared modules.** Helpers are repeated in each notebook that needs them. Notebook 02 Part 9
  holds the whole app in one cell, and later notebooks paste that cell rather than import it. The
  only script is the CI release gate (notebook 13), because CI has to run a file.
- **One baseline run, scored many times.** Notebook 04 runs every golden case through the agent
  once and saves it as `data/golden_runs.json`. Notebooks 04–09 all score that same run, so their
  numbers describe the same behaviour.
- **Free checks before judges.** Each topic starts with a deterministic check in plain Python, then
  adds an LLM judge, then reads the cases where the two disagree.
- **Outputs are committed.** Runs call paid APIs, so you can read every result without running
  anything.

## Module A: The app under test

### Notebook 01: The Knowledge Base and the RAG Agent

**Status:** Run, outputs kept. **Reads:** nothing, as the course starts here. **Writes:**
`data/kb_chunks.json`, `data/chroma_db/`. **Keys:** `OPENROUTER_API_KEY`,
LangSmith.

#### Part 1: The knowledge base
- The store's support articles as the source of truth
- Chunking with stable IDs: `returns-policy-02` names the same text on every run, so test labels
  stay valid

#### Part 2: Indexing and retrieval
- Embedding chunks into a Chroma vector store
- How a question finds the closest chunks

#### Part 3: Grounded answers
- Answers that cite every fact they use
- Declining with "I don't know" when the articles don't cover the question
- Retrieval and answering as two separate decisions, scored separately later

#### Part 4: The RAG agent as a graph
- The retrieve and answer steps as LangGraph nodes, so each one is traceable

#### Part 5: Try it
- Running sample questions
- What a LangSmith trace records per node: inputs, outputs, tokens, cost and time

### Notebook 02: Tools, Agents and the Supervisor Graph

**Status:** Run, outputs kept. **Reads:** `data/chroma_db/`. **Writes:** `data/agent_runs.json`.
**Keys:** `OPENROUTER_API_KEY`, LangSmith.

#### Part 1: The RAG pieces

- Repeated from notebook 01 so this notebook runs alone

#### Part 2: A mock order database
- The store state that tools read and change, and that later notebooks treat as ground truth

#### Part 3: The tools
- `lookup_order`, `issue_refund`, `create_ticket` and `search_kb` as functions the model can call
- Business rules inside the tools: `issue_refund` checks the email, the return window and the
  $500 limit
- Docstrings as instructions: the model chooses tools from their descriptions

#### Part 4: The account agent
- The tool loop: model → tool → model, until the model answers without a tool

#### Part 5: The supervisor and the escalation path
- A structured routing decision that sends each message down one of three paths

#### Part 6: The full graph
- Router, RAG agent, account agent and escalation wired into one LangGraph app

#### Part 7: Recording a run
- Capturing the route, steps, tool calls, retrieved chunks and the database end state
- Two copies of each run: `data/agent_runs.json` for the notebooks, and a LangSmith trace

#### Part 8: Smoke test
- A handful of questions across all paths
- Which recorded field feeds which later evaluation

#### Part 9: The whole app in one cell
- The complete app in a single cell that later notebooks paste in

## Module B: Test data

### Notebook 03: The Golden Set

**Status:** Run, outputs kept. **Reads:** `data/kb_chunks.json`. **Writes:**
`data/golden_set_handwritten.json`, `data/ragas_candidates.json`, `data/golden_set.json`.
**Keys:** `OPENROUTER_API_KEY`. **Evaluations:** §0 test case contract, §1 golden set quality.

#### Part 1: The case schema
- One record per test question, holding the labels for retrieval, routing, tool calls, end state
  and safety
- Labelling only what must match: free-text arguments are left out, and `null` means "not checked"

#### Part 2: The hand-written cases
- Policy rules, unhappy paths and attacks, written by someone who knows the policy
- Stratified slices: six kinds of question, at least 20 each, so each slice can be scored on its own

#### Part 3: Synthetic cases with RAGAS
- Generating extra knowledge questions from the chunks
- The two setting changes RAGAS needed for short chunks

#### Part 4: Reviewing the synthetic cases
- Dropping wrong references, ambiguous questions and near-copies

#### Part 5: Testing the test set
- Five checks before saving: coverage, completeness, synthetic share, duplicates and leakage
- Duplicates: questions compared by embedding cosine similarity, with pairs at 0.95 or above flagged,
  because a near-copy counts the same behaviour twice
- Leakage: no test question may appear in the app's own code. Notebook 02's five smoke questions
  tuned its prompts, so none of them is in the test set

## Module C: RAG evaluation

### Notebook 04: Retrieval Evaluation

**Status:** Run, outputs kept. **Reads:** `data/chroma_db/`, `data/golden_set.json`,
`data/kb_chunks.json`. **Writes:** `data/golden_runs.json` (the baseline run).
**Keys:** `OPENROUTER_API_KEY`. **Evaluations:** §2 ranked
retrieval, §3 judged retrieval.

#### Part 1: The app and the baseline run
- Every golden case through the agent once, saved for notebooks 04–09

#### Part 2: The retriever on its own, scored against labels
- Five metrics in plain Python: hit rate, recall, precision, MRR and nDCG
- Results per slice and per k

#### Part 3: The same numbers from `ranx`
- `ranx` reproducing the hand-written metrics exactly
- `ranx.compare`: a paired significance test showing dense retrieval beats keyword overlap by more
  than chance

#### Part 4: Judged retrieval with RAGAS and DeepEval
- Context precision, recall and relevance with no labels needed
- DeepEval on every case, RAGAS on a 20-case subset, both with the Qwen3 judge

#### Part 5: Where the labels and the judges disagree
- Reading the disagreements: narrow labels, long references, or a judge that misread the chunk

### Notebook 05: Generation Evaluation

**Status:** Run, outputs kept. **Reads:** `data/golden_runs.json`, `data/golden_set.json`,
`data/kb_chunks.json`. **Writes:** `data/rag_scores.json`. **Keys:** `OPENROUTER_API_KEY`. **Evaluations:** §4 reference-free, §5 reference-based, §6 retriever vs
generator blame.

#### Part 1: Which answers to grade
- Picking the knowledge answers from the baseline run

#### Part 2: Did it decline exactly when it should?
- A string compare on the fixed decline sentence: free and exact
- Two directions of error: a missed decline invents policy, while a false decline is unhelpful but
  safe

#### Part 3: Reference-free metrics
- Faithfulness, answer relevancy and hallucination, which need no reference and so also run in
  production
- DeepEval on every answer, RAGAS on a 20-case subset
- Same name, different behaviour: RAGAS and DeepEval relevancy disagree on short cited answers, and
  DeepEval 4.2.3's hallucination score is higher-is-better

#### Part 4: Reference-based metrics
- Exact match and token F1, and why they fail on full sentences
- Factual correctness, semantic similarity, and a `GEval` rubric judge that handle rewording

#### Part 5: Who is to blame?
- Combining recall, faithfulness and correctness to blame each failure on the retriever, the
  generator or the test case

#### Part 6: Save the scores

- Writes every per-case score to `data/rag_scores.json` for the statistics in notebook 12

## Module D: Agent evaluation

### Notebook 06: Tool-Call Evaluation

**Status:** Run (scores are in `data/agent_scores.json`), but the outputs were not saved in the
notebook. **Reads:** `data/chroma_db/`, `data/golden_runs.json`, `data/golden_set.json`.
**Writes:** `data/agent_scores.json`. **Keys:** `OPENROUTER_API_KEY`. **Evaluations:** §7 tool
calls.

#### Part 1: The tools under test

- The app pasted in from notebook 02 Part 9, for the tool schemas and the replay in Part 5
- No model is called: the agent itself is not run here

#### Part 2: Tool selection
- The set of tools called against the set expected
- Why a missing call and an extra call mean different things

#### Part 3: Argument correctness
- Comparing only the arguments the label specifies
- Normalising harmless formatting before matching

#### Part 4: Schema validity and abstention
- Well-formed calls
- No action when the request lacks the information to act on

#### Part 5: Tool results, by replay
- Rebuilding every tool result for free by replaying deterministic tools over a reset store
- Defining an error: a refusal is a rule working, and only a crash is a bug

#### Part 6: The same checks with DeepEval
- `ToolCorrectnessMetric`: deterministic without `available_tools`. By default it ignores extra
  calls and scores every argument key

#### Part 7: An LLM judge for arguments
- `ArgumentCorrectnessMetric`: needs no labels, but can't tell whether a call should have happened

#### Part 8: Save the scores

- Merges each case's scores into `data/agent_scores.json`, keyed by case ID

### Notebook 07: Trajectories and Handoffs

**Status:** Run, outputs kept. **Reads:** `data/golden_runs.json`, `data/golden_set.json`,
`data/agent_scores.json`. **Writes:** `data/agent_scores.json` (merged). **Keys:**
`OPENROUTER_API_KEY`. **Evaluations:** §8 trajectory, §9 routing and handoffs.

#### Part 1: Trajectory matching
- Strict, unordered, subset and superset matches, which say how a path differs as well as whether
  it does

#### Part 2: Step efficiency and loops
- Wasted steps and repeated calls, measured from the run records for free

#### Part 3: A judge for trajectory quality
- A judge that forgives sensible extra steps
- Reading the runs where the judge and the strict match disagree

#### Part 4: Routing accuracy
- Routing as classification: accuracy per slice, and a confusion table for the direction of errors

#### Part 5: Handoffs and escalation
- Escalation as a detector: precision and recall against the cases where the policy requires a
  human

#### Part 6: Context preservation
- A pattern check for order IDs and emails carried across agents
- A judge for everything a pattern can't see

#### Part 7: Which node failed first?
- Blaming the earliest wrong step in the graph, which is where the fix goes

#### Part 8: Save the scores

- Merges trajectory, routing and handoff scores into `data/agent_scores.json`

### Notebook 08: Task Completion and Conversations

**Status:** Run, outputs kept. **Reads:** `data/chroma_db/`, `data/golden_runs.json`,
`data/golden_set.json`, `data/agent_scores.json`. **Writes:** `data/agent_scores.json` (merged),
`data/conversation_scores.json`. **Keys:** `OPENROUTER_API_KEY`, LangSmith.
**Evaluations:** §10 task completion, §11 multi-turn conversation.

#### Part 1: The end-state check
- Comparing the store after a run with the state the case expects
- When a task leaves a mark in the store, the mark is the ground truth

#### Part 2: The app, and the tool results

- The app pasted in from notebook 02 Part 9, so the judges can see tool results and Part 5 can run conversations
- Tool results rebuilt by replaying each run's recorded calls against a fresh store, with tracing paused

#### Part 3: DeepEval `TaskCompletionMetric`
- Telling the judge what "done" means with `task=`, since without it the judge guesses the goal
- Measuring the judge against the end-state check, with every disagreement listed

#### Part 4: RAGAS `AgentGoalAccuracyWithReference`
- A second task-completion judge, checked against the same ground truth

#### Part 5: From messages to conversations
- Passing history through the app's existing `question` and `messages` inputs, with no rewrite
- Scripted conversations for the multi-turn behaviour you thought of
- Four conversational metrics: knowledge retention, completeness, turn relevancy and role
  adherence, read next to the end state

#### Part 6: A simulated customer
- A `gpt-4o-mini` customer that drives new conversations, to find the behaviour nobody scripted

#### Part 7: Save the scores

- Merges task-completion scores into `data/agent_scores.json` and writes `data/conversation_scores.json`

## Module E: Safety

### Notebook 09: Safety and Red-Teaming

**Status:** Run, outputs kept. **Reads:** `data/chroma_db/`, `data/golden_set.json`,
`data/golden_runs.json`, `data/kb_chunks.json`. **Writes:** `data/safety_scores.json`.
**Keys:** `OPENROUTER_API_KEY`, `OPENAI_API_KEY` (moderation), LangSmith. **Evaluations:** §12 safety and
adversarial.

#### Part 1: The safety policy
- Critical violations, which must be zero: moving money without authorisation, exposing another
  customer's data, hijacked instructions and harmful content
- Tracked violations, which are measured and fixed: prompt leaks and rule-breaking replies

#### Part 2: Free checks on every baseline run
- Unauthorised refunds, judged from the mock database's end state, not from the reply
- Leaked emails and leaked system instructions, found by string search

#### Part 3: OpenAI Moderation
- A baseline for generic harm, which never sees this store's business rules

#### Part 4: A judge for the store's own rules
- A `GEval` rubric keyed to each case's policy tags, given both the reply and the actions taken

#### Part 5: Indirect prompt injection
- A poisoned support article with a canary, to test whether retrieved text can take control
- Counting only the runs that actually retrieved the poisoned chunk

#### Part 6: An automated red-team scan with DeepTeam
- Vulnerabilities (what to break) crossed with attack styles (how)
- Running attacks against the real agent through a callback that also records the database

#### Part 7: Attack success rate per risk
- One number per risk, with every critical violation listed

## Module F: Judges and calibration

### Notebook 10: Custom Judges

**Status:** Written, not yet run. **Reads:** `data/golden_set.json`, `data/golden_runs.json`,
`data/golden_runs_gpt-4o-mini.json` (the same 121 cases on the first app model, shipped with the
repository). **Writes:** `data/custom_judge_scores.json`. **Keys:** `OPENROUTER_API_KEY` only, because
nothing here runs the agent. **Evaluations:** §13 custom judges.

#### Part 1: Rubric judges with `GEval`
- House rules no library ships a metric for: tone, policy wording and escalation phrasing
- Writing `evaluation_steps` yourself and reviewing them like code. With `criteria` alone, the judge
  invents its own steps
- `strict_mode=True` for a pass/fail verdict a person can also give, which makes calibration
  possible
- Scoping each rule to the replies it applies to: "not applicable" is not a pass
- A judge beside a free check, and what each one misses

#### Part 2: A decision-tree judge with `DAGMetric`
- Walking the refund flow one small question per node, with a fixed score on each leaf
- Facts about what the agent did come from code, and the judge checks the reply against them
- The reply judge beside the end state: one judges what was said, the other what was done, and a
  release gate needs both

#### Part 3: A pairwise judge, with the positions swapped
- Comparing two app versions answer by answer
- A winner counts only if it wins in both positions, and flips measure position bias

#### Part 4: Save every verdict for calibration

- Writes every verdict and its reason to `data/custom_judge_scores.json`, the input notebook 11 samples for human labels

### Notebook 11: Calibrating Judges with Human Labels

**Status:** Planned. **Writes:** `data/judge_trust.json`. **Evaluations:** §14 judge calibration.

- Sampling 50–100 verdicts per gating judge into a LangSmith annotation queue
- A human labelling pass
- Agreement in plain Python: Cohen's kappa, true-positive rate, true-negative rate and a confusion
  matrix
- Bias checks: position, verbosity, and self-preference (the app model judging its own answers)
- Revising any rubric with kappa below 0.6, then measuring again
- A reference judge: `gpt-4o` beside the Qwen3 judge on the calibration cases, each scored against
  the human labels and the end-state checks, plus judge-vs-judge agreement
- A judge trust table, one row per judge and metric, for the release gate

## Module G: Decisions

### Notebook 12: Statistics, Cost and Experiments

**Status:** Planned. **Writes:** `data/baseline_scores.json`, `data/candidate_scores.json`.
**Evaluations:** §15 statistics and slices, §16 cost and latency, §17 regression experiments.

- A per-slice report across every score from notebooks 04–09
- Bootstrap 95% confidence intervals with the standard library
- Paired comparison of two versions: paired bootstrap and McNemar's test
- How many cases each slice needs to detect a change
- Cost and latency per run, read from LangSmith traces
- The golden set uploaded as a LangSmith dataset
- A baseline and one candidate (a prompt or model change) run as LangSmith experiments

### Notebook 13: The Release Gate and CI

**Status:** Planned. **Writes:** `gate_rules.json`, `gate.py`, a GitHub Actions workflow.
**Evaluations:** §18 release gate.

- Gate rules: zero critical safety violations, slice floors, no regression, judge trust and budget
- The gate logic taught step by step, then copied into the one script CI runs
- A seeded regression that proves the gate fails
- Two CI jobs: a free `gate` job on every push and pull request, and a paid `evaluate` job on manual
  dispatch only

### Notebook 14: Online Evaluation and the Loop

**Status:** Planned. **Evaluations:** §19 online evaluation.

- Simulated production traffic: replayed and fresh questions
- LangSmith online evaluators for faithfulness, relevancy and safety on a 5–10% sample
- Signals that need no answer key: empty retrieval, escalation rate and user feedback
- Drift against launch week
- The loop: failing traces reviewed and added back to the golden set

## Data handoff

| File in `data/` | Written by | Read by |
|---|---|---|
| `kb_chunks.json` | 01 | 03, 04, 05, 09 |
| `chroma_db/` (the search index) | 01 | 02, 04, 06, 08, 09 |
| `agent_runs.json` | 02 | 03 |
| `golden_set.json` | 03 | 04–10 |
| `golden_runs.json` (the baseline run) | 04 | 05–10 |
| `rag_scores.json` | 05 | 12 (planned) |
| `agent_scores.json` | 06, 07, 08 | 07, 08, 12 (planned) |
| `conversation_scores.json` | 08 | 12 (planned) |
| `safety_scores.json` | 09 | 12, 13 (planned) |
| `custom_judge_scores.json` | 10 | 11 (planned) |
| `golden_runs_gpt-4o-mini.json` | shipped with the repository | 10 |

## Tools by notebook

| Tool | Used in |
|---|---|
| LangGraph | 01, 02, and the app cell pasted into later notebooks |
| Chroma | 01, 02 |
| LangSmith | 01, 02 (traces), 08, 09; 11 (annotation queues), 12 (datasets, experiments), 14 (online evaluators) |
| RAGAS | 03 (test-set generation), 04, 05, 08 |
| DeepEval | 04, 05, 06, 07, 08, 09 (`GEval`), 10 (`GEval`, `DAGMetric`) |
| DeepTeam | 09 |
| `ranx` | 04 |
| OpenAI Moderation | 09 |
| Standard library only | Every deterministic check, and the statistics in 11–13 |
