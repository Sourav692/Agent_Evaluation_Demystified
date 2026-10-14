# Evaluation roadmap — agentic applications, basic to expert

The complete ordered path through this repository, by **skill level**. Ten levels in four
bands. Each level lists its topics, goal, notebooks/resources, and a self-check, in that
order. Two dedicated sections follow the levels: the **Databricks / MLflow 3** track as its
own ladder, and what an **OpenAI**-style evaluation round pushes on.

---

## The ladder at a glance

| Band         | Level                                                                                 | The question it answers                                         | Time |
| ------------ | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ---- |
| Beginner     | [0 · Orientation](#level-0-orientation)                                               | What can be measured, and with what kind of scorer?             | 3 h  |
| Beginner     | [1 · RAG](#level-1-rag-retrieval-and-generation)                                      | Did retrieval find it, and did the generator stay inside it?    | 8 h  |
| Intermediate | [2 · Agents](#level-2-agents-tools-conversations-trajectories-outcomes)               | Right tool, right arguments, sound path, goal met?              | 8 h  |
| Intermediate | [3 · Ground truth](#level-3-ground-truth)                                             | Where do the cases and the labels come from?                    | 4 h  |
| Intermediate | [4 · Judges](#level-4-judges-and-the-humans-who-validate-them)                        | Why should anyone believe an LLM's score?                       | 6 h  |
| Advanced     | [5 · Statistics](#level-5-statistics-and-stratified-reporting)                        | Is this change real, and for whom?                              | 4 h  |
| Advanced     | [6 · The gate](#level-6-the-release-gate-and-ci)                                      | Ship or don't ship — and who can loosen that?                  | 5 h  |
| Advanced     | [7 · Online](#level-7-online-evaluation-and-the-loop)                                 | What survives when the answer key is gone?                      | 6 h  |
| Expert       | [8 · Safety and multi-agent](#level-8-safety-adversarial-and-multi-agent-attribution) | What must never happen, and which agent broke it?               | 6 h  |
| Expert       | [9 · The harness](#level-9-the-harness-as-a-product)                                  | How does the evaluation system stay trustworthy and affordable? | 4 h  |

Roughly 54 hours end to end. The [fast paths](#fast-paths) at the bottom cut it to an hour,
an evening, or a weekend.

**Two routes through the same material.** This roadmap is the **Full path**: every level, its
Core and Optional notebooks, and its question-bank sections, in order. The **Core path** is the
short route — only the 21 Core notebooks, course 01 then course 03 — and is listed in
[`courses/README.md`](../../courses/README.md#core-path). Each level's **Path** line says which is which.

---

## Beginner

### Level 0: Orientation

**Topics**

- Evaluation taxonomy: reference-based vs. referenceless
- LLM-judge failure modes and the code-vs-judge decision
- The four-framework map (RAGAS, DeepEval, MLflow, Phoenix)
- Reference-free metrics and their blind spots (ROUGE-L)
- The five-layer diagram: retrieval, generation, tool mechanics, trajectory, outcome
- What breaks where: symptom → metric → cost
- Offline vs. online: the two deciding questions
- The cost ladder: none → key → cached → workspace

**Goal.** Draw the taxonomy from memory and choose between a deterministic scorer and a judge
without hesitating. Every follow-up later is a disguised version of *"which layer are you
measuring?"*

**Notebooks & resources:** [Level 0 mapping →](evaluation-topic-notebook-mapping.md#level-0--orientation)

**Path:** [explainer 00](../roadmap-explainers/00-orientation.md) · **Core:** [c01/00](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) · **Optional:** — · **Question bank:** Part 0 (§0.1–0.3) · **Exit check:** the list below.

**You are done when you can**

- name the five surfaces and, for each, one metric that needs an answer key and one that does not;
- say why *"if code can check it, checking it with a judge is waste"* is a cost argument *and* a reproducibility argument;
- explain in one sentence why reference-based metrics cannot run on production traffic.

### Level 1: RAG (retrieval and generation)

**Topics**

- Deterministic retrieval metrics (Precision@K, Recall@K, MRR, nDCG)
- LLM-judged retrieval metrics (contextual precision, recall, relevancy)
- Referenceless generation metrics (faithfulness, answer relevancy, hallucination)
- Reference-based generation metrics (answer correctness, semantic similarity)
- Evaluation as LangGraph pipeline gates
- RAGAS as a second opinion, and the pytest/CI pattern
- Building a RAG system and synthesizing a golden set
- Writing rubrics that avoid a vague judge

**Goal.** Separate a retrieval failure from a generation failure with numbers, and know the
one failure no referenceless metric can see.

**Notebooks & resources:** [Level 1 mapping →](evaluation-topic-notebook-mapping.md#level-1--rag-retrieval-and-generation)

**Path:** [explainer 01](../roadmap-explainers/01-rag-retrieval-and-generation.md) · **Core:** [c01/01](../../courses/01-rag-agent-tool-evaluation/01_Retrieval_Metrics_Deterministic.ipynb), [c01/02](../../courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb), [c01/03](../../courses/01-rag-agent-tool-evaluation/03_Generator_Metrics_Referenceless.ipynb), [c01/04](../../courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb), [c03/04](../../courses/03-agentic-eval-harness/04_rag_evaluation_with_ragas.ipynb) · **Optional:** [c01/05](../../courses/01-rag-agent-tool-evaluation/05_RAG_Eval_Inside_the_Pipeline.ipynb), [c01/06](../../courses/01-rag-agent-tool-evaluation/06_RAGAS_in_Practice.ipynb), [c01/07](../../courses/01-rag-agent-tool-evaluation/07_RAG_Capstone_Build_and_Evaluate.ipynb) · **Question bank:** Q5, Q8, §10.1–10.3 · **Exit check:** the list below.

**You are done when you can**

- diagnose "low precision" vs "low recall" into two different fixes (reranking / smaller top-k vs chunking / larger top-k / query rewriting);
- explain why groundedness stays satisfied when retrieval was insufficient — and which metric would have caught it;
- say what a "faithful, relevant, and completely wrong" answer is, and why only a reference-based check sees it.

---

## Intermediate

### Level 2: Agents (tools, conversations, trajectories, outcomes)

**Topics**

- Tool-use metrics (tool correctness, argument correctness, tool use)
- Task completion metrics and outcome verification
- Multi-turn conversational evaluation
- Agent trajectory evaluation (the nine trace-level checks)
- Strict vs. loose tool-call matching
- Why per-turn success rates multiply across a conversation

**Goal.** Hold three things apart — mechanics, process, outcome — and reach for the system of
record before any judge.

**Notebooks & resources:** [Level 2 mapping →](evaluation-topic-notebook-mapping.md#level-2--agents-tools-conversations-trajectories-outcomes)

**Path:** [explainer 02](../roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.md) · **Core:** [c01/08](../../courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb), [c01/09](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb), [c01/10](../../courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb), [c01/12](../../courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb), [c03/05](../../courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb) · **Optional:** [c01/11](../../courses/01-rag-agent-tool-evaluation/11_Same_Evals_with_MLflow.ipynb), [c01/14](../../courses/01-rag-agent-tool-evaluation/14_Capstone_CrewAI_Travel_Planner_Eval.ipynb) · **Question bank:** Part 7 (Q26–Q29), §10.4–10.5, Cases 7, 9 · **Exit check:** the list below.

**You are done when you can**

- give three things a task-success metric cannot see (the drill's first rapid-fire question);
- explain why wrong-tool is worse than no-tool, and name a correct behaviour that produces no tool call;
- say why reading a database row beats every LLM-judged metric wherever a side effect exists.

### Level 3: Ground truth

**Topics**

- Golden-set case anatomy (six expectations per case)
- Stratification and the refusal quota
- Dataset datasheets
- Mining production traces into eval datasets
- Provenance and merge-by-input-hash
- Synthesized vs. hand-authored cases

**Goal.** Know where cases and labels come from on day one and by month three, and the two ways
a dataset lies to you.

**Notebooks & resources:** [Level 3 mapping →](evaluation-topic-notebook-mapping.md#level-3--ground-truth)

**Path:** [explainer 03](../roadmap-explainers/03-ground-truth.md) · **Core:** [c03/01](../../courses/03-agentic-eval-harness/01_knowledge_base_and_rag_agent.ipynb), [c03/02](../../courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb), [c03/03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb) · **Optional:** [c02/04](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb) · **Question bank:** Part 3 (Q10–Q13) · **Exit check:** the list below.

**You are done when you can**

- explain *circular ground truth* — why using the agent's own outputs as expectations makes it pass by construction;
- say why hand-written sets are structurally blind, and what a mined set adds that a hand-written one cannot;
- state why a curated set must not drift while a mined set must stay fresh, and why you need both.

### Level 4: Judges, and the humans who validate them

**Topics**

- Building judges three ways (GEval, DAGMetric, rubrics)
- Judge bias: position bias, same-model bias, verbosity
- Human feedback and calibration (Cohen's kappa)
- The rubber-stamp signal
- Custom scorers and trace-based judges
- Judge alignment to expert labels

**Goal.** Build a judge three ways, catch it lying three ways, and know the only thing that
licenses trusting it.

**Notebooks & resources:** [Level 4 mapping →](evaluation-topic-notebook-mapping.md#level-4--judges-and-the-humans-who-validate-them)

**Path:** [explainer 04](../roadmap-explainers/04-judges-and-the-humans-who-validate-them.md) · **Core:** [c03/08](../../courses/03-agentic-eval-harness/08_building_custom_judges.ipynb), [c03/09](../../courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb) · **Optional:** [c02/03](../../courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb), [c02/07](../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb) · **Question bank:** Part 4 (Q14–Q17), Cases 10–12 · **Exit check:** the list below.

**You are done when you can**

- explain why *exact agreement flatters* on skewed distributions and when quadratic weighted kappa is the right default (two judges: identical 0.00 exact agreement, +0.71 vs −0.82 weighted);
- answer "your judge and your domain expert disagree on 20 % of cases" with a procedure, not a shrug;
- say what *rubber-stamping* looks like in the data and why it is a signal about the reviewer, not the agent.

---

## Advanced

### Level 5: Statistics and stratified reporting

**Topics**

- Sample-size math and the bootstrap
- McNemar's test for paired runs
- The small-stratum rule
- Wilson confidence intervals
- Stratified reporting

**Goal.** Refuse to act on a number you cannot resolve, and never report an average that
buries a segment.

**Notebooks & resources:** [Level 5 mapping →](evaluation-topic-notebook-mapping.md#level-5--statistics-and-stratified-reporting)

**Path:** [explainer 05](../roadmap-explainers/05-statistics-and-stratified-reporting.md) · **Core:** [c03/10](../../courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb) · **Optional:** — · **Question bank:** Q4, Q21 · **Exit check:** the list below.

**You are done when you can**

- derive a sample rate from the smallest regression you must catch, rather than from a round number;
- explain why a 58–42 pairwise win rate is not yet a decision;
- pick the groups to stratify by *before* seeing the results, and say what you do with a stratum of eight cases.

### Level 6: The release gate and CI

**Topics**

- The four-check release gate
- Free CI gate vs. paid evaluation job
- Prompt registry and production aliasing
- The two-condition promotion gate
- Optimizer scores vs. the same gate

**Goal.** Turn metrics into a decision that can refuse a deploy, and put the cost of loosening
it on a named line.

**Notebooks & resources:** [Level 6 mapping →](evaluation-topic-notebook-mapping.md#level-6--the-release-gate-and-ci)

**Path:** [explainer 06](../roadmap-explainers/06-the-release-gate-and-ci.md) · **Core:** [c03/11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) · **Optional:** [c02/05](../../courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb), [c02/08](../../courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb) · **Question bank:** Part 6 (Q22–Q25), Cases 13–14 · **Exit check:** the list below.

**You are done when you can**

- explain why a threshold-only gate permits erosion (0.98 → 0.91 clears 0.90) and why a regression-only gate ships a bad baseline's improvement;
- say why the same −0.015 delta blocks on a deterministic metric and is tolerated on a judged one;
- describe a gate that fails a PR without spending a cent, and where the money is spent instead.

### Level 7: Online evaluation and the loop

**Topics**

- Reference-free production metrics
- The five standard alerts
- Incident drills, canaries, and the label queue
- Online-eligibility test for scorers
- Live tracing in Phoenix

**Goal.** Measure without an answer key, alert only on what you can resolve, and carry every
finding back into a gated test.

**Notebooks & resources:** [Level 7 mapping →](evaluation-topic-notebook-mapping.md#level-7--online-evaluation-and-the-loop)

**Path:** [explainer 07](../roadmap-explainers/07-online-evaluation-and-the-loop.md) · **Core:** [c03/12](../../courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb) · **Optional:** [c02/06](../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb), [c01/13](../../courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb) · **Question bank:** Part 5 (Q18–Q20), Case 15 · **Exit check:** the list below.

**You are done when you can**

- give the mechanical test for whether a scorer can run online (does it read `expectations`?);
- name the first alert you would set on a production agent, and why it is not a quality metric;
- state *online discovers, offline prevents recurrence* and give the concrete step that makes it true.

---

## Expert

### Level 8: Safety, adversarial, and multi-agent attribution

**Topics**

- Safety assertions that never get averaged
- Routing confusion matrices and handoff integrity
- Circular-handoff detection and blame attribution
- Adversarial design by attack surface
- Consent and approval gating between turns

**Goal.** Separate what must never happen from what should usually happen, test by attack
surface rather than by example, and say which agent broke a multi-agent run.

**Notebooks & resources:** [Level 8 mapping →](evaluation-topic-notebook-mapping.md#level-8--safety-adversarial-and-multi-agent-attribution)

**Path:** [explainer 08](../roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md) · **Core:** [c03/06](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb), [c03/07](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) · **Optional:** [c02/09](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb), [c02/10](../../courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb) · **Question bank:** Part 8 (Q30–Q32), Cases 8, 16, 17 · **Exit check:** the list below.

**You are done when you can**

- say why a flat list of jailbreak strings tells you nothing when it passes, and what replaces it;
- design the check for "acted without asking" — a failure with no single-turn representation;
- attribute a wrong final answer in a supervisor → specialist run to the routing, the handoff, or the specialist, from the trace alone.

### Level 9: The harness as a product

**Topics**

- Judge/agent model separation and score-mode switches
- Repo conventions: no shared modules, file-based handoff
- Eval-driven development (thresholds before code)
- Open gaps: acceptance criteria, dashboards, canary ladder

**Goal.** Keep the evaluation system itself trustworthy and affordable — the layer above the
metrics.

**Notebooks & resources:** [Level 9 mapping →](evaluation-topic-notebook-mapping.md#level-9--the-harness-as-a-product)

**Path:** [explainer 09](../roadmap-explainers/09-the-harness-as-a-product.md) · **Core:** — (course 03 README: *Cost*, *Conventions*) · **Optional:** [c02/00](../../courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb) · **Question bank:** Part 9 (Q33–Q35), Cases 18–19 · **Exit check:** the list below.

**You are done when you can**

- explain why an unmeasured gate is more dangerous than a failed one, and list four things that report nothing and read as fine;
- say what a hung eval run costs in CI that a failed one does not;
- price a judged evaluation against the traffic it measures, and name the three levers before "use a smaller judge".

---

## Databricks — the MLflow 3 GenAI track as its own ladder

[`courses/02-databricks-mlflow-evals/`](../../courses/02-databricks-mlflow-evals/) builds
one agent (TelcoAssist) in Phase 1 and never meaningfully changes it — every later phase
is about evaluating it. The phases *are* the roadmap: they're order-dependent and reuse
names defined in Phase 0.

**Concept reference:** [`databricks-mlflow-evals.md`](../concepts/databricks-mlflow-evals.md) — Part 2 expands every concept below, Part 4 quantifies it.

**Evaluation regimes:** [`online_vs_offline_evaluation.md`](../concepts/online_vs_offline_evaluation.md) covers the online vs. offline split.

### The phase map

| Tier         | Phases | What it proves                        | Environment                  |
| ------------ | ------ | ------------------------------------- | ---------------------------- |
| Basic        | 0–3   | Tracing and scorers                   | local                        |
| Intermediate | 4–5   | Datasets and gating                   | local                        |
| Advanced     | 6–7   | Online evaluation and judge alignment | workspace                    |
| Expert       | 8–10  | Optimisation and scope                | workspace (8), local (9–10) |

**Notebooks & resources:** [Phase-by-phase mapping →](evaluation-topic-notebook-mapping.md#databricks--phase-by-phase-notebook-mapping)

Two bridges connect back to the framework-agnostic material:

**Bridge (course 01 → MLflow):** [course 01 nb 11](../../courses/01-rag-agent-tool-evaluation/11_Same_Evals_with_MLflow.ipynb) re-asks modules 2.1–2.2's questions through `mlflow.genai.evaluate()`.

**Bridge (multi-turn labs):** [`labs/multiturn-and-tool-eval/`](../../labs/multiturn-and-tool-eval/) runs the same multi-turn and tool metrics in DeepEval and MLflow side by side.

---

### Basic: tracing and scorers (Phases 0–3)

**Topics**

- Writing thresholds and blocking flags before the agent exists — the eval strategy worksheet
- Tracing an agent — autolog plus explicit `@mlflow.trace(span_type=…)`
- Built-in scorers and `mlflow.genai.evaluate()`
- Custom scorers, `make_judge`, and the trace-based (`{{ trace }}`) judge

**Key concepts**

- **Span type is a contract, not a label.** `RetrievalGroundedness()` hard-requires a RETRIEVER span; the wrong type breaks the eval, it does not degrade it.
- **A missing prerequisite errors that row; it does not score 0.** `Correctness()` needs `expected_facts`; on a mixed dataset wrap it to return `None` so the row is skipped, not errored.
- **Exactly six aggregations:** `min`, `max`, `mean`, `median`, `variance`, `p90`. No `p50`, no `p99`, no `sum`.
- **Judge ≠ LLM-judged scorer.** A judge is a model plus a rubric; an LLM-judged scorer is that judge wired into a run and reported as a metric. `make_judge` returns both. "LLM-judged" is a statement about the *number* — it moves between identical runs.
- **Close every `Guidelines` rule with the inapplicable case** — *"if the request asks for none of those things, this guideline is automatically satisfied"* — or it fails on rows where the rule is irrelevant.

**Notebooks & resources:** [Phases 0–3 →](evaluation-topic-notebook-mapping.md#databricks--phase-by-phase-notebook-mapping)

### Intermediate: datasets and gating (Phases 4–5)

**Topics**

- Mining production traces into a managed eval dataset
- Prompt Registry, production aliasing, and rollback as a pointer move
- The two-condition promotion gate and per-metric tolerances
- The eleven quality gates and their thresholds

**Key concepts**

- **Mining gives inputs, not labels.** Novelty-targeting finds the tail; random sampling reproduces the head you already test. Threshold over top-k.
- **Registering is not deploying.** `register_prompt` creates a version; `set_prompt_alias` decides what serves. Rollback is moving a pointer.
- **Two conditions or no.** Every blocking gate clears its threshold *and* no blocking metric drops beyond tolerance vs `@production`. Tolerance **0.00** for deterministic scorers, **0.02** for judged.
- **The eleven quality gates** — `safety`, `account_protection`, `approval_gate` at 1.00; `groundedness`, `tool_call_correctness`, `escalation`, `tool_selection` at 0.90; `correctness`, `relevance`, `context_retention` at 0.85; `conciseness` at 0.70 and *not* blocking. Three resolve only on conversation runs and must report **not measured**, never 0.

**Notebooks & resources:** [Phases 4–5 →](evaluation-topic-notebook-mapping.md#databricks--phase-by-phase-notebook-mapping)

### Advanced: online evaluation and judge alignment (Phases 6–7)

**Topics**

- Traces in Unity Catalog and sampled live scorers
- The mechanical online-eligibility test
- Sampling economics — choosing a rate from the delta you must detect
- Judge alignment to expert labels (MemAlign)

**Key concepts**

- **The online-eligibility test is mechanical: does the scorer read `expectations`?** `Safety`, `RelevanceToQuery`, `RetrievalGroundedness`, `Guidelines` and deterministic checks transfer; `Correctness`, `ExpectationsGuidelines`, `tool_call_correctness` do not.
- **Register *and* start.** A registered-but-unstarted scorer evaluates nothing and looks identical to a working one.
- **Sample judges, never sample deterministic scorers.** Choose the rate from the delta you must detect: a two-point drop needs ~606 scored traces — 30 % of 2,000/day, not 5 %.
- **Agreement, not average score.** Quadratic weighted kappa for ordinal scales. The label schema name must equal the judge name or `align()` silently learns nothing. A falling score after alignment is the success condition.

**Notebooks & resources:** [Phases 6–7 →](evaluation-topic-notebook-mapping.md#databricks--phase-by-phase-notebook-mapping)

### Expert: optimisation and scope (Phases 8–10)

**Topics**

- Automated prompt optimisation with GEPA
- Session-level metrics, tool selection vs. tool use, and approval gating
- Adversarial design by attack surface (the capstone)

**Key concepts**

- **The judge is the objective.** GEPA optimises toward whatever the judge rewards; an unaligned judge makes optimisation actively harmful. A higher optimisation score is the most overfit number available — it goes through the same gate, scored on a strictly larger scorer set.
- **Scope of validity.** A scorer correct for a one-tool agent becomes misleading when the agent gains a second tool; with two tools, wrong-tool is worse than no-tool.
- **Consent lives between turns.** Compliant, violation, and *stalled* (agreed but nothing happened) need different fixes.
- **Three ideas that recur:** aggregates hide the thing you need to see · every measurement has a scope of validity · silence and success look identical.

**Notebooks & resources:** [Phases 8–10 →](evaluation-topic-notebook-mapping.md#databricks--phase-by-phase-notebook-mapping)

---

### Vocabulary crosswalk

**Notebooks & resources:** [Three-vocabularies mapping →](evaluation-topic-notebook-mapping.md#databricks--the-same-idea-in-three-vocabularies) — RAGAS/DeepEval term ↔ MLflow scorer ↔ what it asks.

### Watch out for — environment realities

- Phases 0–5 and 9–10 run locally against `sqlite:///mlflow.db`. It must be a **database** backend, not `file://` — the Prompt Registry requires it. Set `TELCOASSIST_PROVIDER=openai` to avoid a Databricks-served endpoint.
- Phases 6–8 need a workspace, a CLI profile, a SQL warehouse ID and a Unity Catalog schema you can create tables in. `ALL_PRIVILEGES` is explicitly *not* sufficient for UC trace tables — see the course `PLAN.md`.
- Phase 7 needs a human willing to be the domain-expert labeller. It can be you.
- `langgraph` is pinned to `1.2.11`; resolving `mlflow` can pull it back to `1.0.x` and break every LangGraph notebook. Re-pin, don't float.
- Read the reference's [Part 3](../concepts/databricks-mlflow-evals.md) — 32 gotchas — starting with section **A, silent failures**. Every one returns a clean run and a wrong number.

### You are done when you can

- state the online-eligibility test from memory, and name which built-in scorers transfer and which don't;
- explain why registering a prompt isn't deploying it, and what moves the pointer that decides what serves;
- say why a higher optimisation score is the most overfit number available, and what gate it still has to clear;
- name the three ideas that recur across all ten phases — aggregates hide the thing you need to see, every measurement has a scope of validity, silence and success look identical.

**Rehearsal:** [Q14–Q17](../interview-prep/QUESTION_BANK.md) (judges), [Q18–Q21](../interview-prep/QUESTION_BANK.md) (online), [Q22–Q23](../interview-prep/QUESTION_BANK.md) (gating, the optimiser), [Cases 4, 10, 11, 15](../interview-prep/QUESTION_BANK.md).

**Lines worth saying out loud:** [Part 4](../concepts/databricks-mlflow-evals.md) has the sampling line, the judges line, and the erosion line.

If you want one module in the Databricks skill catalogue to cross-check API shapes
against, it is `databricks-mlflow-evaluation`; the notebooks here are the ground truth for
what each call actually does.

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

| Axis                      | Weak                              | Strong                                                                                      |
| ------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------- |
| Ambiguity handling        | Draws a RAG diagram in minute two | Spends 5–8 minutes on who the user is, what the workflow costs, what "good" is numerically |
| Decomposition             | "The agent does X"                | Named components with contracts, each independently measurable and failable                 |
| Measurement discipline    | "We'd use RAGAS"                  | Separates the five surfaces; says which are blocking vs informational                       |
| Failure reasoning         | Assumes the happy path            | Names the blast radius of each wrong decision; designs so the model is allowed to be wrong  |
| Judgment under constraint | Says yes to the goal              | Pushes back with a reason and an alternative sequencing                                     |

### 2. The answer skeleton

The eight-step **Decomposition Spine** ([§0.2](../interview-prep/QUESTION_BANK.md)):
clarify → define "good" numerically → decompose → pick the measurement per component →
design the ground truth → design the gate → design the rollout by risk tier → design the
feedback loop. Two lines to say while drawing it: *online discovers, offline prevents
recurrence*; *the gate is the only thing that can deploy* — machine-written prompts included.

### 3. The two follow-ups to expect

See [the follow-up mapping →](evaluation-topic-notebook-mapping.md#openai-round--follow-up-mapping)
for where each of the two standard follow-ups ("you have no labelled data", "what's the
smallest launchable thing") is answered in this repo.

### 4. Vocabulary to have ready

The repo evaluates LangGraph and CrewAI systems; the Agents SDK concepts map one-to-one onto
what the notebooks measure. See [the vocabulary mapping →](evaluation-topic-notebook-mapping.md#openai-round--vocabulary-mapping).

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

## Fast paths

| You have                              | Do                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **One hour**                    | Course 01:[nb 00](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) → [nb 02](../../courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb) → [nb 09](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb) → [nb 12](../../courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb). Or, entirely free: the five [interactive labs](../interactive-labs/) |
| **One evening**                 | Tutorial §7's four: define good ([course 01 nb 00](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb)), build the set ([course 03 nb 03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb)), judge it ([nb 08](../../courses/03-agentic-eval-harness/08_building_custom_judges.ipynb)), refuse to ship ([nb 11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb))                 |
| **One weekend**                 | Levels 0–2 with the labs, then Level 6 read-only. You can now draw the taxonomy, argue mechanics ≠ process ≠ outcome, and describe a gate                                                                                                                                                                                                                                                                                              |
| **Two weeks**                   | All ten levels in order, running what you can afford. Course 03's own hour is[01](../../courses/03-agentic-eval-harness/01_knowledge_base_and_rag_agent.ipynb) → [03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb) → [04](../../courses/03-agentic-eval-harness/04_rag_evaluation_with_ragas.ipynb) → [11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb)                                       |
| **An interview, not a subject** | [The study plan](evaluation-study-plan.html), then the OpenAI or Databricks section above, then [the drill](../interview-prep/evaluation-round-drill.html)                                                                                                                                                                                                                                                                                  |

**Where the money goes.** Course 01 nb 01 and the interactive labs are free; the rest of
course 01 needs a key. Course 02 phases 0–5 and 9–10 spend on an LLM endpoint; 6–8 need a
workspace. Course 03 notebooks 01, 02, 04, 05 and 06 generate live; 03 and 09–12 read files
and cost nothing; judge verdicts are cached after the first run. Never run a bare `pytest` at
the repo root — it sweeps up every paid batch script.

---

## Special mention

Three paths through this repo exist; pick by intent.

| Path                                                                                  | Ordered by                                            | Use it when                                     |
| ------------------------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------- |
| **This roadmap**                                                                | skill level — nothing assumed, expert at the end     | You want the subject, not just the round        |
| [`evaluation-study-plan.html`](evaluation-study-plan.html)                           | what an interview round tests, most-decisive first    | You have an eval-heavy round in under two weeks |
| [`openai-eval-guide-tutorial.md` §7](../guide-audits/openai-eval-guide-tutorial.md) | shortest route that still holds up — eight notebooks | You have one evening                            |
