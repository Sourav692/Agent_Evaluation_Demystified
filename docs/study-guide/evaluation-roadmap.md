# Evaluation roadmap — agentic applications, basic to expert

The complete ordered path through this repository, by **skill level**. Ten levels in four
bands, each with what to read or run, what it teaches, what it costs, and a check you can
apply to yourself before moving on. Two dedicated sections follow the levels: what an
**OpenAI**-style evaluation round pushes on, and the **Databricks / MLflow 3** track as its own
ladder.

Three paths through this repo exist; pick by intent.

| Path | Ordered by | Use it when |
|---|---|---|
| **This roadmap** | skill level — nothing assumed, expert at the end | You want the subject, not just the round |
| [`evaluation-study-plan.html`](evaluation-study-plan.html) | what an interview round tests, most-decisive first | You have an eval-heavy round in under two weeks |
| [`openai-eval-guide-tutorial.md` §7](../guide-audits/openai-eval-guide-tutorial.md) | shortest route that still holds up — eight notebooks | You have one evening |

**Reading the tables.** *Cost* is what running the item spends: **none** — no API calls;
**key** — live `OPENAI_API_KEY` calls; **cached** — judged once, replayed from
`data/score_cache/` afterwards; **workspace** — a real Databricks workspace. Everything under
`docs/` is free. Times are for reading and running, not mastering. Notebook paths are
relative to this file; they paste into `jupyter lab` from the repo root once you drop the
`../../`.

---

## The ladder at a glance

| Band | Level | The question it answers | Time |
|---|---|---|---|
| Beginner | [0 · Orientation](#level-0-orientation) | What can be measured, and with what kind of scorer? | 3 h |
| Beginner | [1 · RAG](#level-1-rag-retrieval-and-generation) | Did retrieval find it, and did the generator stay inside it? | 8 h |
| Intermediate | [2 · Agents](#level-2-agents-tools-conversations-trajectories-outcomes) | Right tool, right arguments, sound path, goal met? | 8 h |
| Intermediate | [3 · Ground truth](#level-3-ground-truth) | Where do the cases and the labels come from? | 4 h |
| Intermediate | [4 · Judges](#level-4-judges-and-the-humans-who-validate-them) | Why should anyone believe an LLM's score? | 6 h |
| Advanced | [5 · Statistics](#level-5-statistics-and-stratified-reporting) | Is this change real, and for whom? | 4 h |
| Advanced | [6 · The gate](#level-6-the-release-gate-and-ci) | Ship or don't ship — and who can loosen that? | 5 h |
| Advanced | [7 · Online](#level-7-online-evaluation-and-the-loop) | What survives when the answer key is gone? | 6 h |
| Expert | [8 · Safety and multi-agent](#level-8-safety-adversarial-and-multi-agent-attribution) | What must never happen, and which agent broke it? | 6 h |
| Expert | [9 · The harness](#level-9-the-harness-as-a-product) | How does the evaluation system stay trustworthy and affordable? | 4 h |

Roughly 54 hours end to end. The [fast paths](#fast-paths) at the bottom cut it to an hour,
an evening, or a weekend.

---

## Beginner

### Level 0: Orientation

**Goal.** Draw the taxonomy from memory and choose between a deterministic scorer and a judge
without hesitating. Every follow-up later is a disguised version of *"which layer are you
measuring?"*

| Read / run | Teaches | Cost |
|---|---|---|
| [`00_Evaluation_Landscape.ipynb`](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) | The taxonomy, reference-based vs referenceless, judge failure modes, the code-vs-judge decision (§4), the four-framework map (§5), and §1c — why ROUGE-L scores a false answer 0.94 and a true one 0.09 | none |
| [Field guide, Part 0](../concepts/rag-agent-tool-evaluation.md) | §0.1b *what breaks where* — one row per surface, symptom → metric → cost. §0.2 the two questions that decide offline vs online. §0.4 the cost ladder | none |
| [`00-evaluation-index.html`](../interactive-labs/00-evaluation-index.html) | The surface map as a page: pipeline, what breaks where, reference-based vs referenceless | none |
| [Question bank §0.3](../interview-prep/QUESTION_BANK.md) | The five-layer diagram — retrieval, generation, tool mechanics, trajectory, outcome — with end-state verification as the strongest signal | none |

**You are done when you can**

- name the five surfaces and, for each, one metric that needs an answer key and one that does not;
- say why *"if code can check it, checking it with a judge is waste"* is a cost argument *and* a reproducibility argument;
- explain in one sentence why reference-based metrics cannot run on production traffic.

### Level 1: RAG (retrieval and generation)

**Goal.** Separate a retrieval failure from a generation failure with numbers, and know the
one failure no referenceless metric can see.

| Read / run | Teaches | Cost |
|---|---|---|
| [`01_Retrieval_Metrics_Deterministic.ipynb`](../../courses/01-rag-agent-tool-evaluation/01_Retrieval_Metrics_Deterministic.ipynb) + [lab 01](../interactive-labs/01-deterministic-retrieval-metrics.html) | Precision@K, Recall@K, MRR, nDCG. Drag K: precision moves non-monotonically, recall stalls at 0.67, MRR never moves | none |
| [`02_Retrieval_Metrics_LLM_Judged.ipynb`](../../courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb) + [lab 02](../interactive-labs/02-llm-judged-retrieval-metrics.html) | Contextual precision / recall / relevancy — three metrics because there are three failures. Reordering chunks drops precision alone | key |
| [`03_Generator_Metrics_Referenceless.ipynb`](../../courses/01-rag-agent-tool-evaluation/03_Generator_Metrics_Referenceless.ipynb) + [lab 03](../interactive-labs/03-generator-metrics.html) | Faithfulness, answer relevancy, hallucination. The answer that scores 1.00 on both while being flatly false | key |
| [`04_Generator_Metrics_Reference_Based.ipynb`](../../courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb) | Answer correctness via `GEval` — `criteria` and `evaluation_steps` forms — and semantic similarity | key |
| [Field guide §1.5](../concepts/rag-agent-tool-evaluation.md) | Writing a rubric that does not produce a vague judge | none |
| [`05_RAG_Eval_Inside_the_Pipeline.ipynb`](../../courses/01-rag-agent-tool-evaluation/05_RAG_Eval_Inside_the_Pipeline.ipynb) | Evaluation as LangGraph nodes — gates inside the pipeline, not scoring after it | none (mocked), key (real) |
| [`06_RAGAS_in_Practice.ipynb`](../../courses/01-rag-agent-tool-evaluation/06_RAGAS_in_Practice.ipynb) | RAGAS as a second opinion on the same case, and the pytest / CI pattern | key |
| [`07_RAG_Capstone_Build_and_Evaluate.ipynb`](../../courses/01-rag-agent-tool-evaluation/07_RAG_Capstone_Build_and_Evaluate.ipynb) | Build a RAG system, synthesise a golden set, run the whole suite | key |
| [Field guide Part 6, §6.1–6.3](../concepts/rag-agent-tool-evaluation.md) | The slow narrative behind labs 01–03, against the same numbers | none |

**You are done when you can**

- diagnose "low precision" vs "low recall" into two different fixes (reranking / smaller top-k vs chunking / larger top-k / query rewriting);
- explain why groundedness stays satisfied when retrieval was insufficient — and which metric would have caught it;
- say what a "faithful, relevant, and completely wrong" answer is, and why only a reference-based check sees it.

---

## Intermediate

### Level 2: Agents (tools, conversations, trajectories, outcomes)

**Goal.** Hold three things apart — mechanics, process, outcome — and reach for the system of
record before any judge.

| Read / run | Teaches | Cost |
|---|---|---|
| [`09_Tool_Use_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb) + [lab 04](../interactive-labs/04-tool-use-evaluation.html) | `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ToolUseMetric`. Five broken traces all score 1.00 until `should_exact_match=True`, then 0.17 | key |
| [`10_Task_Completion_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb) | `TaskCompletionMetric`, custom rubrics, outcome verification | key |
| [`08_MultiTurn_Conversational_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb) | `ConversationalGEval`, turn relevancy, knowledge retention, simulated conversations | key |
| [`12_Agent_Trajectory_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb) + [lab 05](../interactive-labs/05-agent-trajectory-evaluation.html) | The nine trace-level checks on a refund agent. Five of nine never move; task success passes on 40 % waste | none (Parts A–B), key (Part C) |
| [Field guide Parts 2–3](../concepts/rag-agent-tool-evaluation.md) | §2.1 why per-turn rates multiply · §2.2 strict vs loose matching · §2.4 the polite tool failure · §3.2 the three trajectory traps | none |
| [Databricks ref, Part 4 — `p ** n`](../concepts/databricks-mlflow-evals.md) | At 95 % per turn a conversation is more likely failed than not by turn 14 | none |
| [`labs/multiturn-and-tool-eval/`](../../labs/multiturn-and-tool-eval/) *(optional)* | The same multi-turn and tool metrics twice — DeepEval and MLflow — side by side. Its own `uv` project | key |

**You are done when you can**

- give three things a task-success metric cannot see (the drill's first rapid-fire question);
- explain why wrong-tool is worse than no-tool, and name a correct behaviour that produces no tool call;
- say why reading a database row beats every LLM-judged metric wherever a side effect exists.

### Level 3: Ground truth

**Goal.** Know where cases and labels come from on day one and by month three, and the two ways
a dataset lies to you.

| Read / run | Teaches | Cost |
|---|---|---|
| [`03_the_golden_set.ipynb`](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb) | Case anatomy — six expectations, not one · strata by language and intent · the 20 % refusal quota · the datasheet. *Everything downstream is an opinion about this file* | none |
| [`04_eval_datasets_from_traces.ipynb`](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb) | Mining production traces: novelty-targeting over random sampling, threshold over top-k, provenance (`AssessmentSource`), merge by input hash. Mining gives inputs, not labels | key |
| [Field guide §1.8](../concepts/rag-agent-tool-evaluation.md) | Golden datasets — what to synthesise and what must be authored | none |
| [Question bank Part 3](../interview-prep/QUESTION_BANK.md) | Q10 day one → month three · Q11 eval set and traffic diverging · Q12 how big · Q13 who writes the labels | none |

**You are done when you can**

- explain *circular ground truth* — why using the agent's own outputs as expectations makes it pass by construction;
- say why hand-written sets are structurally blind, and what a mined set adds that a hand-written one cannot;
- state why a curated set must not drift while a mined set must stay fresh, and why you need both.

### Level 4: Judges, and the humans who validate them

**Goal.** Build a judge three ways, catch it lying three ways, and know the only thing that
licenses trusting it.

| Read / run | Teaches | Cost |
|---|---|---|
| [`08_building_custom_judges.ipynb`](../../courses/03-agentic-eval-harness/08_building_custom_judges.ipynb) | `GEval` vs `DAGMetric` vs rubrics · position bias and same-model bias, measured · the verbosity audit and length-controlled probe | cached |
| [`09_human_feedback_and_calibration.ipynb`](../../courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb) | Three kinds of human feedback · Cohen's kappa by hand · the rubber-stamp signal · blinded preference testing | none |
| [`03_custom_scorers_and_judges.ipynb`](../../courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb) | `@scorer`, `make_judge`, the trace-based judge (`{{ trace }}`) — judging *how* the agent worked | key |
| [`07_judge_alignment_memalign.ipynb`](../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb) | Aligning a judge to expert labels; measuring agreement, never average score; why a falling score is success | workspace |
| [Field guide §0.3](../concepts/rag-agent-tool-evaluation.md) | LLM-as-judge failure modes | none |
| [Tutorial §4](../guide-audits/openai-eval-guide-tutorial.md) | Code vs judge vs human · the three judge biases · kappa · blinded preference, in 3–4 lines each with a TODO | none |
| [Question bank Part 4](../interview-prep/QUESTION_BANK.md) | Q14 why believe the number · Q15 20 % disagreement · Q16 when not to use a judge · Q17 judge says 0.9, customer says terrible | none |

**You are done when you can**

- explain why *exact agreement flatters* on skewed distributions and when quadratic weighted kappa is the right default (two judges: identical 0.00 exact agreement, +0.71 vs −0.82 weighted);
- answer "your judge and your domain expert disagree on 20 % of cases" with a procedure, not a shrug;
- say what *rubber-stamping* looks like in the data and why it is a signal about the reviewer, not the agent.

---

## Advanced

### Level 5: Statistics and stratified reporting

**Goal.** Refuse to act on a number you cannot resolve, and never report an average that
buries a segment.

| Read / run | Teaches | Cost |
|---|---|---|
| [`10_stratified_reporting_and_statistics.ipynb`](../../courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb) | Sample size · McNemar for paired runs · the bootstrap in ten lines of stdlib · the small-stratum rule | none |
| [`stratified-reporting-explained.html`](../interview-prep/stratified-reporting-explained.html) | One table: overall 87.5 % → 90 % while Hindi collapses 88 % → 50 % | none |
| [Online vs offline §5](../concepts/online_vs_offline_evaluation.md) | The sampling-resolution problem; §5.1 in plain English | none |
| [Databricks ref, Part 4 — the numbers](../concepts/databricks-mlflow-evals.md) | Wilson intervals: ±0.045 at 100 traces, ±0.018 at 600. A two-point drop needs ~606 scored traces — 30 % of 2,000/day, not 5 % | none |
| [Question bank Q4, Q21](../interview-prep/QUESTION_BANK.md) | "One number for a dashboard" · "a metric dropped two points" | none |

**You are done when you can**

- derive a sample rate from the smallest regression you must catch, rather than from a round number;
- explain why a 58–42 pairwise win rate is not yet a decision;
- pick the groups to stratify by *before* seeing the results, and say what you do with a stratum of eight cases.

### Level 6: The release gate and CI

**Goal.** Turn metrics into a decision that can refuse a deploy, and put the cost of loosening
it on a named line.

| Read / run | Teaches | Cost |
|---|---|---|
| [`11_the_release_gate_and_ci.ipynb`](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) | Four checks in order — safety, aggregate floor, per-stratum floor, cost ceiling — and four scenarios | none |
| [`ci/apply_gate.py`](../../courses/03-agentic-eval-harness/ci/apply_gate.py) + [`release-gate.yml`](../../.github/workflows/release-gate.yml) | The free, stdlib-only decision layer, and why the paid `evaluate` job is *not* on the merge path | none |
| [`05_prompt_versioning_and_regression.ipynb`](../../courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb) | Registering ≠ deploying · alias as rollback · the two-condition gate · tolerance 0.00 deterministic, 0.02 judged | key |
| [`08_automated_improvement_gepa.ipynb`](../../courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb) | An optimised prompt passes the *same* gate, scored on a superset of what it optimised | workspace |
| [`launch-gate.html`](../concepts/launch-gate.html) | The gate on one page | none |
| [Question bank Part 6, Case 13, Case 14](../interview-prep/QUESTION_BANK.md) | Safe to ship · the optimiser's higher score · a green dashboard that is wrong · Case 13 designs the CI gate | none |

**You are done when you can**

- explain why a threshold-only gate permits erosion (0.98 → 0.91 clears 0.90) and why a regression-only gate ships a bad baseline's improvement;
- say why the same −0.015 delta blocks on a deterministic metric and is tolerated on a judged one;
- describe a gate that fails a PR without spending a cent, and where the money is spent instead.

### Level 7: Online evaluation and the loop

**Goal.** Measure without an answer key, alert only on what you can resolve, and carry every
finding back into a gated test.

| Read / run | Teaches | Cost |
|---|---|---|
| [`12_online_evaluation_and_the_loop.ipynb`](../../courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb) | Reference-free metrics · five alerts · incident drills · the canary · the label queue that closes the loop | none |
| [`06_online_eval_production_monitoring.ipynb`](../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb) | Traces as tables · sampled live scorers · register *and* start · the mechanical online-eligibility test | workspace |
| [Online vs offline](../concepts/online_vs_offline_evaluation.md) | The two regimes, what flows between them, where human alignment fits | none |
| [Field guide Part 4](../concepts/rag-agent-tool-evaluation.md) | §4.1 what can never go online · §4.2 sampling and alerting · §4.3 what tracing adds | none |
| [`13_Production_Grade_Agent_Eval_Overview.ipynb`](../../courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb) → [Arize labs](../../labs/agent-evaluation/arize-phoenix-labs/) *(optional)* | Live tracing plus offline experiments in Phoenix — the one framework built around traces rather than test cases | key + Phoenix |
| [`rag-vs-support-eval-walkthrough.html`](../concepts/rag-vs-support-eval-walkthrough.html) | Offline, online and the gate walked through on two real systems | none |
| [Question bank Part 5, Case 15](../interview-prep/QUESTION_BANK.md) | Q18 offline vs online · Q19 what to sample · Q20 beyond a quality score · Case 15 sets up monitoring | none |

**You are done when you can**

- give the mechanical test for whether a scorer can run online (does it read `expectations`?);
- name the first alert you would set on a production agent, and why it is not a quality metric;
- state *online discovers, offline prevents recurrence* and give the concrete step that makes it true.

---

## Expert

### Level 8: Safety, adversarial, and multi-agent attribution

**Goal.** Separate what must never happen from what should usually happen, test by attack
surface rather than by example, and say which agent broke a multi-agent run.

| Read / run | Teaches | Cost |
|---|---|---|
| [`07_safety_and_policy_checks.ipynb`](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) | Assertions that block absolutely and are never averaged · why a flaky safety test is a safety problem | cached |
| [`06_agent_handoff_and_end_to_end.ipynb`](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb) | Routing confusion matrix · handoff integrity · circular-handoff detection · trajectory matching · the SQLite final-state check · blame attribution | key |
| [`10_capstone_edge_cases_and_crossref.ipynb`](../../courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb) | Design by attack surface: classes × variants · behavioural boundaries · channel confusion · the polite tool failure · stating N/A with a reason | key |
| [`09_multiturn_and_tool_selection.ipynb`](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) | Consent lives between turns · three approval outcomes · gate by prompt, verify by evaluation · gates that must report *not measured*, never 0 | key |
| [`eval-harness-two-usecases.html`](../concepts/eval-harness-two-usecases.html) | The same harness on an enterprise RAG agent and on a tool-calling multi-agent system, side by side | none |
| [Field guide Part 5](../concepts/rag-agent-tool-evaluation.md) | Handoff quality, nested traces, attribution | none |
| [Question bank Part 8, Cases 8, 16, 17](../interview-prep/QUESTION_BANK.md) | Adversarial sets worth having · evidence for legal · "we tested 15 jailbreak strings and passed 12" · "the agent must never do X" | none |

**You are done when you can**

- say why a flat list of jailbreak strings tells you nothing when it passes, and what replaces it;
- design the check for "acted without asking" — a failure with no single-turn representation;
- attribute a wrong final answer in a supervisor → specialist run to the routing, the handoff, or the specialist, from the trace alone.

### Level 9: The harness as a product

**Goal.** Keep the evaluation system itself trustworthy and affordable — the layer above the
metrics.

| Read / run | Teaches | Cost |
|---|---|---|
| [Course 03 README — *Cost*, *Judge verdicts are cached*, *Fault switches*](../../courses/03-agentic-eval-harness/README.md) | The judge runs on a different model than the agent (`gpt-4.1-mini`, 6 of 6 calls at ~2.5 s vs a 248 s runaway) · `SCORE_MODE` auto / strict / record · a cache that exists for comparability, not savings · twelve faults that all return a fluent 200 | none |
| [Course 03 README — *Conventions*](../../courses/03-agentic-eval-harness/README.md) | No shared modules, files in `data/` as the handoff, no pandas — every number traceable from the notebook that produced it | none |
| [`00_eval_strategy_worksheet.ipynb`](../../courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb) | Thresholds and blocking flags written before the agent exists — eval-driven development as a worksheet | none |
| [`genai-eval-playbook-coverage-map.md`](../guide-audits/genai-eval-playbook-coverage-map.md) | What this repo does *not* build: acceptance criteria with sign-off owners, stakeholder dashboards, the staged canary ladder, retrieval operations. Thirteen open gaps, clustered | none |
| [`fde-playbook-end-to-end-evaluation.html`](../interview-prep/fde-playbook-end-to-end-evaluation.html) | The customer-facing version of the whole pipeline: dataset sizes by stage, the canary ladder with rollback triggers, four dashboard views | none |
| [Question bank Part 9, Cases 18, 19](../interview-prep/QUESTION_BANK.md) | Q33 cost · Q34 ownership · Q35 is the eval system still working · Case 18 build the platform · Case 19 cost is 4× | none |

**You are done when you can**

- explain why an unmeasured gate is more dangerous than a failed one, and list four things that report nothing and read as fine;
- say what a hung eval run costs in CI that a failed one does not;
- price a judged evaluation against the traffic it measures, and name the three levers before "use a smaller judge".

---

## OpenAI — what the round pushes on

The core decomposition is identical everywhere; what differs is the follow-up you get pushed
hardest on. For OpenAI-style rounds the tilt is **ambiguity → scoped use case → architecture
→ eval → production, in that order**, with evaluation treated as a product surface rather
than a QA activity ([question bank, Appendix C](../interview-prep/QUESTION_BANK.md)).

### 1. What is being scored

Five axes, from [question bank §0.1](../interview-prep/QUESTION_BANK.md). The single
highest-signal behaviour is treating evaluation as a **design input**: if you cannot say how
you would measure a component, you have not finished designing it.

| Axis | Weak | Strong |
|---|---|---|
| Ambiguity handling | Draws a RAG diagram in minute two | Spends 5–8 minutes on who the user is, what the workflow costs, what "good" is numerically |
| Decomposition | "The agent does X" | Named components with contracts, each independently measurable and failable |
| Measurement discipline | "We'd use RAGAS" | Separates the five surfaces; says which are blocking vs informational |
| Failure reasoning | Assumes the happy path | Names the blast radius of each wrong decision; designs so the model is allowed to be wrong |
| Judgment under constraint | Says yes to the goal | Pushes back with a reason and an alternative sequencing |

### 2. The answer skeleton

The eight-step **Decomposition Spine** ([§0.2](../interview-prep/QUESTION_BANK.md)):
clarify → define "good" numerically → decompose → pick the measurement per component →
design the ground truth → design the gate → design the rollout by risk tier → design the
feedback loop. Two lines to say while drawing it: *online discovers, offline prevents
recurrence*; *the gate is the only thing that can deploy* — machine-written prompts included.

### 3. The two follow-ups to expect, and where the repo answers them

| Follow-up | The answer lives in |
|---|---|
| **"You have no labelled data. What do you ship in week one?"** | Referenceless checks first — faithfulness, relevancy, safety, deterministic assertions ([field guide §1.3, §0.2](../concepts/rag-agent-tool-evaluation.md); [course 03 nb 07](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb)). Log everything and mine later ([course 02 nb 01](../../courses/02-databricks-mlflow-evals/01_minimal_agent_and_tracing.ipynb) → [nb 04](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb)). A small stratified golden set with a refusal quota before the first judge ([course 03 nb 03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb)). Spoken form: [Q10](../interview-prep/QUESTION_BANK.md), [Q7](../interview-prep/QUESTION_BANK.md) |
| **"What's the smallest thing you could launch that produces a measurable business number?"** | Rollout by risk tier — assistive → gated-write → autonomous — not by calendar (Spine step 7; [Case 3](../interview-prep/QUESTION_BANK.md)). End-state verification as the business number where a side effect exists ([§0.3 of the bank](../interview-prep/QUESTION_BANK.md); [course 03 nb 06](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb)). What to challenge when the ask is "launch next week": [Q32](../interview-prep/QUESTION_BANK.md), [Q4](../interview-prep/QUESTION_BANK.md) |

### 4. Vocabulary to have ready, mapped to what you practised here

The repo evaluates LangGraph and CrewAI systems; the Agents SDK concepts map one-to-one onto
what the notebooks measure.

| OpenAI term | The evaluation you already know |
|---|---|
| `Handoff` | Routing confusion matrix, handoff integrity, circular-handoff detection, blame attribution — [course 03 nb 06](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb); [field guide Part 5](../concepts/rag-agent-tool-evaluation.md) |
| `Guardrail` | Assertions that block and are never averaged — [course 03 nb 07](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb); approval gating tested rather than assumed — [course 02 nb 09](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) |
| `Session` / multi-turn | Session-level vs turn-level, context retention, `p ** n` — [course 01 nb 08](../../courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb); [course 02 nb 09](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) |
| Built-in **file search** | Retrieval metrics with and without labels — Level 1 |
| Function tools | Tool selection vs argument correctness, strict vs loose — [course 01 nb 09](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb); [course 03 nb 05](../../courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb) |
| Structured outputs | Deterministic scorers over a parseable output — the cheapest rung of the cost ladder ([field guide §0.4](../concepts/rag-agent-tool-evaluation.md)) |
| Evals as a product surface | A gate that returns *ship / don't ship*, wired to CI — [course 03 nb 11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) |

### 5. OpenAI's own evaluation guide, measured against this repo

[`openai-eval-guide-coverage-gaps.md`](../guide-audits/openai-eval-guide-coverage-gaps.md)
badges every topic in OpenAI's *Evaluation best practices* guide against the notebook that
teaches it, per course: **47 covered, 2 partial, 5 descoped, 1 gap** across 55 rows. The
guide's eleven edge cases are mapped in `edge_cases.py` and
[course 02 nb 10](../../courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb).
[`openai-eval-guide-tutorial.md`](../guide-audits/openai-eval-guide-tutorial.md) is the
same guide as a lesson — 21 TODOs that each ask you to produce something.

**What you must learn outside this repo.** The one open gap is OpenAI's own **Evals API and
Graders** — the vendor surface. The ideas transfer intact (a grader is a scorer; a run is an
`evaluate()` call), but the API is not taught here. Also not here by design: industry
benchmarks, multimodal evaluation, reinforcement fine-tuning, and computer-use / code-interpreter
evaluation — every system in this repo is text-only.

### 6. Rehearsal

1. [The study plan](evaluation-study-plan.html) — seven stages, 17–25 hours, a 2–3 day fast path and a skip list.
2. [The drill](../interview-prep/evaluation-round-drill.html) — the 35 questions and 19 cases with answers hidden; rate your recall.
3. [Appendix D](../interview-prep/QUESTION_BANK.md) — 23 rapid-fire questions at 60–90 seconds each.
4. [Appendix E](../interview-prep/QUESTION_BANK.md) — what gets people marked down, and seven lines worth having ready.

**Three days, OpenAI-flavoured.** Day 1: Level 0, the Spine, Q1–Q4, Q10. Day 2: Levels 2 and
4 read-only, Cases 1–3 out loud, Q32. Day 3: Levels 6 and 7 read-only, Case 13, the drill
filtered to weak items, Appendix D.

---

## Databricks — the MLflow 3 GenAI track as its own ladder

[`courses/02-databricks-mlflow-evals/`](../../courses/02-databricks-mlflow-evals/) builds one
agent (TelcoAssist) in Phase 1 and never meaningfully changes it; every later phase is about
evaluating it. The phases *are* the roadmap — they are order-dependent and reuse names defined
in Phase 0. The reference for random access is
[`databricks-mlflow-evals.md`](../concepts/databricks-mlflow-evals.md); the two regimes are in
[`online_vs_offline_evaluation.md`](../concepts/online_vs_offline_evaluation.md).

### 1. The stack, phase by phase

| Phase | Notebook | What it proves | Runs |
|---|---|---|---|
| 0 | [`00_eval_strategy_worksheet`](../../courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb) | `AGENT_SPEC`, `EVAL_DIMENSIONS`, `QUALITY_GATES` — thresholds and blocking flags before any code | local |
| 1 | [`01_minimal_agent_and_tracing`](../../courses/02-databricks-mlflow-evals/01_minimal_agent_and_tracing.ipynb) | An untraceable agent is unevaluable. Autolog plus explicit `@mlflow.trace(span_type=…)`; retrieval as a fixed step so every trace has a RETRIEVER span | local |
| 2 | [`02_offline_eval_fundamentals`](../../courses/02-databricks-mlflow-evals/02_offline_eval_fundamentals.ipynb) | `mlflow.genai.evaluate()`, built-in scorers, prerequisites, gates as a ship decision | local |
| 3 | [`03_custom_scorers_and_judges`](../../courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb) | `@scorer`, `make_judge`, the `{{ trace }}` judge, the low-level `judges` API | local |
| 4 | [`04_eval_datasets_from_traces`](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb) | Mining traces into a managed dataset; provenance; merge by input hash | local |
| 5 | [`05_prompt_versioning_and_regression`](../../courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb) | Prompt Registry, `@production` alias, the two-condition promotion gate | local |
| 6 | [`06_online_eval_production_monitoring`](../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb) | Traces in Unity Catalog, sampled live scorers, sampling economics | **workspace** |
| 7 | [`07_judge_alignment_memalign`](../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb) | MemAlign: agreement, not average; distilled guidelines as the real output | **workspace** |
| 8 | [`08_automated_improvement_gepa`](../../courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb) | `optimize_prompts()`; the optimised prompt passes Phase 5's gate on a scorer superset | **workspace** |
| 9 | [`09_multiturn_and_tool_selection`](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) | Session-level metrics, tool selection ≠ tool use, approval gating, gate scope | local |
| 10 | [`10_capstone_edge_cases_and_crossref`](../../courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb) | Adversarial design by attack surface; the OpenAI edge-case coverage map | local |

Two bridges from the framework-agnostic material:
[course 01 nb 11](../../courses/01-rag-agent-tool-evaluation/11_Same_Evals_with_MLflow.ipynb)
re-asks modules 2.1–2.2's questions through `mlflow.genai.evaluate()`, and
[`labs/multiturn-and-tool-eval/`](../../labs/multiturn-and-tool-eval/) runs the same
multi-turn and tool metrics in DeepEval and MLflow side by side.

### 2. Concepts you must be able to state — by level

Every line here is expanded in the reference's [Part 2](../concepts/databricks-mlflow-evals.md)
and quantified in [Part 4](../concepts/databricks-mlflow-evals.md).

**Basic — tracing and scorers (Phases 1–3)**

- **Span type is a contract, not a label.** `RetrievalGroundedness()` hard-requires a RETRIEVER span; the wrong type breaks the eval, it does not degrade it.
- **A missing prerequisite errors that row; it does not score 0.** `Correctness()` needs `expected_facts`; on a mixed dataset wrap it to return `None` so the row is skipped, not errored.
- **Exactly six aggregations:** `min`, `max`, `mean`, `median`, `variance`, `p90`. No `p50`, no `p99`, no `sum`.
- **Judge ≠ LLM-judged scorer.** A judge is a model plus a rubric; an LLM-judged scorer is that judge wired into a run and reported as a metric. `make_judge` returns both. "LLM-judged" is a statement about the *number* — it moves between identical runs.
- **Close every `Guidelines` rule with the inapplicable case** — *"if the request asks for none of those things, this guideline is automatically satisfied"* — or it fails on rows where the rule is irrelevant.

**Intermediate — datasets and gating (Phases 4–5)**

- **Mining gives inputs, not labels.** Novelty-targeting finds the tail; random sampling reproduces the head you already test. Threshold over top-k.
- **Registering is not deploying.** `register_prompt` creates a version; `set_prompt_alias` decides what serves. Rollback is moving a pointer.
- **Two conditions or no.** Every blocking gate clears its threshold *and* no blocking metric drops beyond tolerance vs `@production`. Tolerance **0.00** for deterministic scorers, **0.02** for judged.
- **The eleven quality gates** — `safety`, `account_protection`, `approval_gate` at 1.00; `groundedness`, `tool_call_correctness`, `escalation`, `tool_selection` at 0.90; `correctness`, `relevance`, `context_retention` at 0.85; `conciseness` at 0.70 and *not* blocking. Three resolve only on conversation runs and must report **not measured**, never 0.

**Advanced — online and alignment (Phases 6–7)**

- **The online-eligibility test is mechanical: does the scorer read `expectations`?** `Safety`, `RelevanceToQuery`, `RetrievalGroundedness`, `Guidelines` and deterministic checks transfer; `Correctness`, `ExpectationsGuidelines`, `tool_call_correctness` do not.
- **Register *and* start.** A registered-but-unstarted scorer evaluates nothing and looks identical to a working one.
- **Sample judges, never sample deterministic scorers.** Choose the rate from the delta you must detect: a two-point drop needs ~606 scored traces — 30 % of 2,000/day, not 5 %.
- **Agreement, not average score.** Quadratic weighted kappa for ordinal scales. The label schema name must equal the judge name or `align()` silently learns nothing. A falling score after alignment is the success condition.

**Expert — optimisation and scope (Phases 8–10)**

- **The judge is the objective.** GEPA optimises toward whatever the judge rewards; an unaligned judge makes optimisation actively harmful. A higher optimisation score is the most overfit number available — it goes through the same gate, scored on a strictly larger scorer set.
- **Scope of validity.** A scorer correct for a one-tool agent becomes misleading when the agent gains a second tool; with two tools, wrong-tool is worse than no-tool.
- **Consent lives between turns.** Compliant, violation, and *stalled* (agreed but nothing happened) need different fixes.
- **Three ideas that recur:** aggregates hide the thing you need to see · every measurement has a scope of validity · silence and success look identical.

### 3. The same idea in three vocabularies

| RAGAS / DeepEval | MLflow | Asks |
|---|---|---|
| Contextual relevancy / context precision | `RetrievalRelevance` | Is each retrieved chunk relevant? |
| Context recall | `RetrievalSufficiency` | Do the chunks contain everything the answer needs? |
| Faithfulness | `RetrievalGroundedness` | Is the answer supported by what was retrieved? |
| Answer relevancy | `RelevanceToQuery` | Does the answer address the question? |
| Answer correctness | `Correctness` | Is it right against a reference? |

### 4. Environment realities

- Phases 0–5 and 9–10 run locally against `sqlite:///mlflow.db`. It must be a **database** backend, not `file://` — the Prompt Registry requires it. Set `TELCOASSIST_PROVIDER=openai` to avoid a Databricks-served endpoint.
- Phases 6–8 need a workspace, a CLI profile, a SQL warehouse ID and a Unity Catalog schema you can create tables in. `ALL_PRIVILEGES` is explicitly *not* sufficient for UC trace tables — see the course `PLAN.md`.
- Phase 7 needs a human willing to be the domain-expert labeller. It can be you.
- `langgraph` is pinned to `1.2.11`; resolving `mlflow` can pull it back to `1.0.x` and break every LangGraph notebook. Re-pin, don't float.
- Read the reference's [Part 3](../concepts/databricks-mlflow-evals.md) — 32 gotchas — starting with section **A, silent failures**. Every one returns a clean run and a wrong number.

### 5. Databricks-flavoured rehearsal

[Q14–Q17](../interview-prep/QUESTION_BANK.md) (judges), [Q18–Q21](../interview-prep/QUESTION_BANK.md)
(online), [Q22–Q23](../interview-prep/QUESTION_BANK.md) (gating, the optimiser),
[Cases 4, 10, 11, 15](../interview-prep/QUESTION_BANK.md), and the reference's
[Part 4 — *Lines worth being able to say out loud*](../concepts/databricks-mlflow-evals.md):
the sampling line, the judges line, the erosion line. If you want one module in the Databricks
skill catalogue to cross-check API shapes against, it is `databricks-mlflow-evaluation`; the
notebooks here are the ground truth for what each call actually does.

---

## Fast paths

| You have | Do |
|---|---|
| **One hour** | Course 01: [nb 00](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) → [nb 02](../../courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb) → [nb 09](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb) → [nb 12](../../courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb). Or, entirely free: the five [interactive labs](../interactive-labs/) |
| **One evening** | Tutorial §7's four: define good ([course 01 nb 00](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb)), build the set ([course 03 nb 03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb)), judge it ([nb 08](../../courses/03-agentic-eval-harness/08_building_custom_judges.ipynb)), refuse to ship ([nb 11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb)) |
| **One weekend** | Levels 0–2 with the labs, then Level 6 read-only. You can now draw the taxonomy, argue mechanics ≠ process ≠ outcome, and describe a gate |
| **Two weeks** | All ten levels in order, running what you can afford. Course 03's own hour is [01](../../courses/03-agentic-eval-harness/01_knowledge_base_and_rag_agent.ipynb) → [03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb) → [04](../../courses/03-agentic-eval-harness/04_rag_evaluation_with_ragas.ipynb) → [11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) |
| **An interview, not a subject** | [The study plan](evaluation-study-plan.html), then the OpenAI or Databricks section above, then [the drill](../interview-prep/evaluation-round-drill.html) |

**Where the money goes.** Course 01 nb 01 and the interactive labs are free; the rest of
course 01 needs a key. Course 02 phases 0–5 and 9–10 spend on an LLM endpoint; 6–8 need a
workspace. Course 03 notebooks 01, 02, 04, 05 and 06 generate live; 03 and 09–12 read files
and cost nothing; judge verdicts are cached after the first run. Never run a bare `pytest` at
the repo root — it sweeps up every paid batch script.
