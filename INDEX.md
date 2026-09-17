# Document index

A lookup table, not a starting point. `README.md` answers *"where do I begin?"*; this file
answers **"I need to know about X — which file, and which section of it?"**

Everything here is prose or notebooks. Nothing on this page executes.

---

## 1. Find it by topic

**The four short names used in every table below:**

| Short name | Is this file | What it is |
|---|---|---|
| **Field guide** | [`docs/concepts/rag-agent-tool-evaluation.md`](docs/concepts/rag-agent-tool-evaluation.md) | Course 01 theory. Tool-agnostic: what each check catches and misses, no framework APIs |
| **Question bank** | [`docs/interview-prep/QUESTION_BANK.md`](docs/interview-prep/QUESTION_BANK.md) | 35 questions + 25 metric questions + 19 cases + appendices |
| **Databricks ref** | [`docs/concepts/databricks-mlflow-evals.md`](docs/concepts/databricks-mlflow-evals.md) | Course 02 theory. Framework-specific: MLflow scorers, gotchas, the numbers |
| **Drill page** | [`docs/interview-prep/evaluation-round-drill.html`](docs/interview-prep/evaluation-round-drill.html) | The self-quiz. Open in a browser |

`§` is a section number inside that file — **§1.1** is the field guide's section 1.1, **§6.1**
its section 6.1. Jump to the section rather than scrolling. `lab 0N-…` means
[`docs/interactive-labs/`](docs/interactive-labs/)`0N-*.html`.

### Retrieval

| Looking for | Go to |
|---|---|
| Precision@K, Recall@K, MRR, nDCG — formulas and what each catches | Field guide **§1.1**; worked through with real numbers in **§6.1** |
| Why four metrics instead of one, and the recall plateau | Field guide **§6.1**; interactive `01-deterministic-retrieval-metrics.html` |
| Contextual Precision / Recall / Relevancy (judged, no labels) | Field guide **§1.2**, worked in **§6.2**; lab `02-…` |
| Which retrieval metrics need an answer key | Field guide **§0.2** |
| Retrieval metric interview questions | Question bank **§10.1**, **§10.2** |

### Generation

| Looking for | Go to |
|---|---|
| Faithfulness, answer relevancy, hallucination (no reference needed) | Field guide **§1.3**, worked in **§6.3**; lab `03-…` |
| Answer correctness, `GEval`, semantic similarity (reference needed) | Field guide **§1.4** |
| Writing a rubric that doesn't produce a vague judge | Field guide **§1.5**; MLflow version in Databricks ref **Part 4** |
| "Faithful, relevant, and completely wrong" — the failure no referenceless metric sees | Field guide **§6.3** |

### Tools, trajectory, outcome

| Looking for | Go to |
|---|---|
| Tool selection, argument correctness, strict vs loose matching | Field guide **§2.2**, worked in **§6.4**; lab `04-…` |
| Task completion vs tool mechanics — why both | Field guide **§2.3** |
| The nine trace-level trajectory checks | Field guide **§3.1**, worked in **§6.5**; lab `05-…` |
| End-state verification (reading the system of record) | Field guide **§3.1**, **§0.1b** |
| Multi-turn conversation, and why per-turn rates multiply | Field guide **§2.1**; question bank **Q26**, **Q27** |
| Multi-agent systems and handoff attribution | Field guide **Part 5**; question bank **Case 8** |

### Choosing and running checks

| Looking for | Go to |
|---|---|
| **What breaks where** — one row per surface, symptom → metric → cost | Field guide **§0.1b** |
| Reference-based vs referenceless, and why it decides offline/online | Field guide **§0.2** |
| Deterministic scorer or LLM judge? | Notebook `00_Evaluation_Landscape` **§4**; drill page Stage 01 |
| LLM-as-judge failure modes | Field guide **§0.3** |
| Cost ladder — cheapest thing that answers the question | Field guide **§0.4** |
| Which framework is for what (DeepEval / RAGAS / MLflow / Phoenix) | `docs/interactive-labs/README.md`; notebook `00_…` **§5** |

### Production and release

| Looking for | Go to |
|---|---|
| Offline vs online, and what can never go online | Field guide **§4.1**; question bank **Q18** |
| Sampling rates and alerting | Field guide **§4.2**; Databricks ref **Part 4** |
| Release gating — thresholds *and* no-regression | Question bank **Part 6**, **Case 13**; course 03 notebook **11** (four checks, four scenarios) |
| A gate as a decision layer rather than another metric | Course 03 notebook **11**; `courses/03-agentic-eval-harness/ci/apply_gate.py` |
| Stratified reporting — gating on the worst segment, not the mean | Course 03 notebooks **04** and **10** |
| Evaluating the human approval step itself (rubber-stamping) | Course 03 notebook **09** |
| Final-state checks against a database ("exactly once") | Course 03 notebook **06** |
| Silent failures that look like success | Databricks ref **Part 3**; question bank **Appendix A** |
| Judge alignment, agreement measures, quadratic weighted kappa | Databricks ref **Part 4**; question bank **Q15**, **Case 10** |
| Wilson intervals, sample size, "is this drop real?" | Databricks ref **Part 4**; question bank **Q21** |
| Cost control | Question bank **Part 9**, **Case 19** |

### Interview preparation

| Looking for | Go to |
|---|---|
| A reading path with time estimates | `evaluation-study-plan.html` |
| Self-quiz with hidden answers and per-item scoring | `evaluation-round-drill.html` |
| 35 situational questions | Question bank **Parts 1–9** |
| 25 metric-level questions | Question bank **Part 10** |
| 19 long-form cases | Question bank **Tiers A–H** |
| The Decomposition Spine (8 steps) | Question bank **§0.2** |
| Same 19 cases in Bengali | `QUESTION_BANK_cases_bn.md` |

---

## 2. The documents

### `docs/concepts/rag-agent-tool-evaluation.md` — Field guide (13,700 words)

The theory companion to course 01. Tool-agnostic on purpose: no framework APIs, no code.
**The single best place to look up what a check catches and what it misses.**

| | Covers |
|---|---|
| **Part 0 — The Map** | 0.1 what you can evaluate · 0.1b what breaks where · 0.2 the two questions that decide everything · 0.3 LLM-as-judge failure modes · 0.4 the cost ladder · 0.5 a note on frameworks |
| **Part 1 — RAG** | 1.1 retrieval with labels · 1.2 retrieval without labels · 1.3 generation without a reference · 1.4 generation against a reference · 1.5 writing a rubric · 1.6 evaluation inside the pipeline · 1.7 running it in batch · 1.8 golden datasets · 1.9 reading the results |
| **Part 2 — Conversation, tools, task** | 2.1 multi-turn · 2.2 tool use · 2.3 task completion · 2.4 polite tool failure · quick lookup table |
| **Part 3 — Trajectory** | 3.1 the nine checks · 3.2 three traps · 3.3 what each looks like on a live system |
| **Part 4 — Production** | 4.1 offline/online split · 4.2 sampling and alerting · 4.3 what tracing adds · 4.4 two genuinely new ideas |
| **Part 5 — Multi-agent** | Handoff quality, nested traces, attribution |
| **Part 6 — The worked labs** | 6.1–6.5, the slow narrative version of each interactive lab, against real numbers |
| **Quick Reference** | Debugging loop · question → measurement · one-page cheat sheet · the five that matter most |

### `docs/concepts/databricks-mlflow-evals.md` — Databricks/MLflow reference (9,900 words)

The theory companion to course 02. Framework-specific, where the field guide is not.

| | Covers |
|---|---|
| **Part 1** | TelcoAssist, the agent under test: tools, data, models, trace shape, deliberate non-goals |
| **Part 2** | Concept map by theme, each pointing at the phase that demonstrates it. Appendix A: what this track measures (built-in scorers, guidelines, quality gates). Appendix B: the wider metric landscape and the naming map across three vocabularies |
| **Part 3** | 32 gotchas as symptom → cause → fix, led by the silent failures |
| **Part 4** | The numbers, thresholds, decision rules, scorer prerequisites, agreement measures, phase map |

### `docs/interview-prep/QUESTION_BANK.md` — Question bank (25,300 words)

Everything for the evaluation thread of a system-design round, in one file.

| | Covers |
|---|---|
| **Part 0** | What the round measures (five scoring axes) · the Decomposition Spine · the evaluation taxonomy |
| **Parts 1–9** | 35 questions. Each: the issue underneath, what they're checking, a strong answer, a weak answer *with why it reads badly*, and the follow-up to expect |
| **Part 10** | 25 metric-level questions, grouped by evaluation surface — the ones asked with your dashboard on screen |
| **Tiers A–H** | 19 cases, 30–45 minutes each: strategy from zero · diagnosing production · trajectory and multi-agent · judges and calibration · gating and CI · monitoring · adversarial · platform |
| **Appendices A–E** | Silent-failure catalogue · misreadings that sound like insight · company-specific flavour · rapid-fire drill · closing notes |

### The three interactive HTML pages

Open in a browser. No build step, no server, no API key.

| File | What it does |
|---|---|
| `docs/interview-prep/evaluation-study-plan.html` | Seven stages ordered by what the round tests, with time estimates, a 2–3 day fast path, a skip list and a readiness check. Tick items off as you go |
| `docs/interview-prep/evaluation-round-drill.html` | The same 35 questions and 19 cases with every answer hidden. Rate recall per item, filter to what's weak. Progress saves locally |
| `docs/interactive-labs/00-evaluation-index.html` | The surface map: pipeline, what breaks where, reference-based vs referenceless comparison |

### The five interactive labs

`docs/interactive-labs/0N-*.html` — change the inputs, watch the metrics move. The written
version of each is field guide **Part 6**; the interview questions are question bank **Part 10**.

| Lab | The thing it shows you |
|---|---|
| `01-deterministic-retrieval-metrics` | Drag K: precision moves non-monotonically, recall stalls at 0.67, MRR never moves |
| `02-llm-judged-retrieval-metrics` | Reordering three chunks — adding and removing nothing — drops precision alone |
| `03-generator-metrics` | An answer scoring 1.00 faithfulness *and* 1.00 relevancy while being flatly false |
| `04-tool-use-evaluation` | Five broken traces all score 1.00 until you set `should_exact_match=True`, then 0.17 |
| `05-agent-trajectory-evaluation` | Five of nine metrics never move; task success reports a clean pass on 40% waste |

### Folder indexes

| File | What it indexes |
|---|---|
| `docs/README.md` | The three docs subfolders |
| `docs/concepts/README.md` | The two theory companions |
| `docs/interactive-labs/README.md` | The six labs, the surface map, lab → notebook mapping, the four tools |
| `docs/interview-prep/README.md` | Study plan, drill, question bank, and the shape of a good answer |

---

## 3. The notebooks

### `courses/01-rag-agent-tool-evaluation/` — 15 notebooks, sequential

| Notebook | Covers | Theory in |
|---|---|---|
| `00_Evaluation_Landscape` | Taxonomy, reference-based vs referenceless, judge failure modes, **§4 code-vs-judge scorer choice**, tooling map | Field guide Part 0 |
| `01_Retrieval_Metrics_Deterministic` | Precision@K, Recall@K, MRR, nDCG | §1.1, §6.1 |
| `02_Retrieval_Metrics_LLM_Judged` | Contextual Precision / Recall / Relevancy | §1.2, §6.2 |
| `03_Generator_Metrics_Referenceless` | Faithfulness, answer relevancy, hallucination | §1.3, §6.3 |
| `04_Generator_Metrics_Reference_Based` | Answer correctness via `GEval`, semantic similarity | §1.4 |
| `05_RAG_Eval_Inside_the_Pipeline` | Evaluation as LangGraph nodes — gates, not after-the-fact scoring | §1.6 |
| `06_RAGAS_in_Practice` | RAGAS quickstart, multi-metric, the pytest/CI pattern | §1.7 |
| `07_RAG_Capstone_Build_and_Evaluate` | Build a RAG system, synthesize a golden dataset, run the full suite | §1.8 |
| `08_MultiTurn_Conversational_Evaluation` | `ConversationalGEval`, turn relevancy, knowledge retention | §2.1 |
| `09_Tool_Use_Evaluation` | `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ToolUseMetric` | §2.2, §6.4 |
| `10_Task_Completion_Evaluation` | `TaskCompletionMetric`, custom rubrics, outcome verification | §2.3 |
| `11_Same_Evals_with_MLflow` | The same questions via `mlflow.genai.evaluate()` over traces | Field guide Part 2 + Databricks ref |
| `12_Agent_Trajectory_Evaluation` | The 9-metric trace-level suite on a refund-agent scenario | Part 3, §6.5 |
| `13_Production_Grade_Agent_Eval_Overview` | Live tracing + offline experiments (Arize Phoenix) | Part 4 |
| `14_Capstone_CrewAI_Travel_Planner_Eval` | Task completion against a real running 3-agent app | Part 5 |

### `courses/02-databricks-mlflow-evals/` — 11 notebooks, order-dependent

Phases 0–5 and 9–10 run locally on `sqlite:///mlflow.db`. Phases 6–8 need a real workspace.

| Notebook | Covers |
|---|---|
| `00_eval_strategy_worksheet` | `AGENT_SPEC`, `EVAL_DIMENSIONS`, `QUALITY_GATES` — names every later phase reuses |
| `01_minimal_agent_and_tracing` | The agent under test, and getting traces out of it |
| `02_offline_eval_fundamentals` | `mlflow.genai.evaluate()`, built-in scorers, scorer prerequisites |
| `03_custom_scorers_and_judges` | `@scorer` functions, `make_judge`, trace-based judges |
| `04_eval_datasets_from_traces` | Mining production traces into a dataset |
| `05_prompt_versioning_and_regression` | Prompt registry, threshold + no-regression gating |
| `06_online_eval_production_monitoring` | Sampling, live scorers, monitoring |
| `07_judge_alignment_memalign` | Aligning a judge to expert judgement; why a falling score is success |
| `08_automated_improvement_gepa` | `optimize_prompts()`, and why an optimised prompt still passes the same gate |
| `09_multiturn_and_tool_selection` | Session-level quality, tool-selection correctness |
| `10_capstone_edge_cases_and_crossref` | Adversarial and edge-case evaluation |

Supporting modules (`agent.py`, `scorers.py`, `promotion.py`, `monitoring.py`, `conversation.py`,
`eval_dataset.py`, `alignment.py`, `edge_cases.py`, `traffic.py`, `trace_view.py`) are shared and
mutable across phases — the notebooks import from them rather than redefining.

### `courses/03-agentic-eval-harness/` — 12 notebooks, sequential

The subject is the harness and the release gate; the agent ("Lumen Cloud", a LangGraph
supervisor over four specialists) exists only to be measured. **All 12 notebooks are complete.** with final titles, objectives, concepts and data contracts. Notebooks hand
off through files in `data/` and never import from each other — the inverse of course 02.

Replay caches make 03–12 free and deterministic: `FIXTURE_MODE` replays generations,
`SCORE_MODE` replays judge verdicts. Only `tests/test_release_gate.py` and `"record"` mode
cost money.

| Notebook | Covers | Produces |
|---|---|---|
| `01_knowledge_base_and_rag_agent` | 40 multilingual articles, chunking, Chroma, hybrid retrieval, cite-or-refuse | `data/chroma/` |
| `02_tools_agents_and_supervisor_graph` | SQLite ground truth, approval-gated writes, LangGraph, the trajectory dict, record-and-replay | `data/lumen.db`, `data/fixtures/` |
| `03_the_golden_set` | Case anatomy (six expectations, not one), strata, the 20% refusal quota, the datasheet | `data/golden_set.json` |
| `04_rag_evaluation_with_ragas` | RAGAS 0.4 collections API, citation accuracy as a regex vs. a rubric, per-language reporting | `data/rag_report.json` |
| `05_tool_call_evaluation` *(stub)* | Level 1: `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ok`/`empty`/`unavailable` | `data/tool_report.json` |
| `06_agent_handoff_and_end_to_end` *(stub)* | Levels 2–3: routing confusion matrix, handoff integrity, trajectory matching, SQLite final-state check, blame attribution | `data/agent_report.json` |
| `07_safety_and_policy_checks` *(stub)* | Assertions that block absolutely; why a flaky safety test is a safety problem | `data/safety_report.json` |
| `08_building_custom_judges` *(stub)* | `GEval` vs. `DAGMetric` vs. rubrics; position bias and same-model bias | `data/judge_comparison.json` |
| `09_human_feedback_and_calibration` *(stub)* | Three kinds of human feedback, Cohen's kappa by hand, the rubber-stamp signal | `data/human_labels.jsonl` |
| `10_stratified_reporting_and_statistics` *(stub)* | Sample size, McNemar, bootstrap — stdlib only, no pandas | `data/baseline_report.json` |
| `11_the_release_gate_and_ci` *(stub)* | Four gate checks, four scenarios, `tests/test_release_gate.py`, the two-job workflow | `data/gate_result.json` |
| `12_online_evaluation_and_the_loop` *(stub)* | Reference-free metrics, five alerts, incident drills, canary, closing the loop | `data/online_report.json` |

Non-notebook files: `ci/apply_gate.py` (the free, stdlib-only decision layer),
`tests/test_release_gate.py` (**paid**, LLM-driven), and
`.github/workflows/release-gate.yml` (two jobs — the expensive one is deliberately not on the
merge path).

---

## 4. `labs/` — raw source material

Unnumbered on purpose; order doesn't matter. Reach for these when a course points at one, or
when you want the unabridged version. Each folder has its own `README.md`.

| Folder | What's in it |
|---|---|
| `rag-evaluation/` | DeepEval metric drills, RAGAS scripts, a FastAPI RAG bot, Streamlit demos |
| `agent-evaluation/arize-phoenix-labs/` | DeepLearning.AI × Arize — 5 progressive tracing/eval labs. Third-party, kept verbatim |
| `agent-evaluation/crewai-travel-planner/` | A real 3-agent CrewAI app used as an evaluation target |
| `langgraph-agent-rag-eval/` | 9-metric trace-level suite, interview-prep framing |
| `multiturn-and-tool-eval/` | Multi-turn + tool metrics, DeepEval vs MLflow side by side. **Its own uv project** — `uv sync` inside it |
| `llm-as-judge/` | G-Eval smoke test |

---

## 5. `archive/`

Superseded material, kept rather than deleted. `archive/README.md` is a manifest with a row per
file explaining what replaced it. Nothing in `courses/`, `labs/` or `docs/` depends on it. Worth
opening only when you want to see how something used to be organised.

---

## Keeping this file honest

This index names **sections**, not line numbers, so it survives edits to a document's body. It
breaks when a section is renumbered or a file is renamed. If you move or rename anything under
`docs/` or `courses/`, re-check this file along with the folder READMEs —
`python3 .claude/skills/link-check/scripts/check_links.py` catches broken links but not a
section reference that has silently become wrong.
