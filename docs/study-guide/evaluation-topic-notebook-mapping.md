# Topic & notebook mapping

The lookup companion to [`evaluation-roadmap.md`](evaluation-roadmap.md). That file carries the
narrative — goal and self-check per level; this file carries every **topic → notebook/resource →
cost** table, so neither document has to hold both jobs. Notebook paths are relative to this
file; they paste into `jupyter lab` from the repo root once you drop the `../../`.

**Cost key.** **none** — no API calls; **key** — live `OPENAI_API_KEY` calls; **cached** —
judged once, replayed from `data/score_cache/` afterwards; **workspace** — a real Databricks
workspace. Everything under `docs/` is free.

---

## Level 0 · Orientation

| Read / run | Teaches | Cost |
|---|---|---|
| [`00_Evaluation_Landscape.ipynb`](../../courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb) | The taxonomy, reference-based vs referenceless, judge failure modes, the code-vs-judge decision (§4), the four-framework map (§5), and §1c — why ROUGE-L scores a false answer 0.94 and a true one 0.09 | none |
| [Field guide, Part 0](../concepts/rag-agent-tool-evaluation.md) | §0.1b *what breaks where* — one row per surface, symptom → metric → cost. §0.2 the two questions that decide offline vs online. §0.4 the cost ladder | none |
| [`00-evaluation-index.html`](../interactive-labs/00-evaluation-index.html) | The surface map as a page: pipeline, what breaks where, reference-based vs referenceless | none |
| [Question bank §0.3](../interview-prep/QUESTION_BANK.md) | The five-layer diagram — retrieval, generation, tool mechanics, trajectory, outcome — with end-state verification as the strongest signal | none |

## Level 1 · RAG (retrieval and generation)

| Read / run | Teaches | Cost |
|---|---|---|
| [`01_Retrieval_Metrics_Deterministic.ipynb`](../../courses/01-rag-agent-tool-evaluation/01_Retrieval_Metrics_Deterministic.ipynb) + [lab 01](../interactive-labs/01-deterministic-retrieval-metrics.html) | Precision@K, Recall@K, MRR, nDCG. Drag K: precision moves non-monotonically, recall stalls at 0.67, MRR never moves | none |
| [`02_Retrieval_Metrics_LLM_Judged.ipynb`](../../courses/01-rag-agent-tool-evaluation/02_Retrieval_Metrics_LLM_Judged.ipynb) + [lab 02](../interactive-labs/02-llm-judged-retrieval-metrics.html) | Contextual precision / recall / relevancy — three metrics because there are three failures. Reordering chunks drops precision alone | key |
| [`03_Generator_Metrics_Referenceless.ipynb`](../../courses/01-rag-agent-tool-evaluation/03_Generator_Metrics_Referenceless.ipynb) + [lab 03](../interactive-labs/03-generator-metrics.html) | Faithfulness, answer relevancy, hallucination. The answer that scores 1.00 on both while being flatly false | key |
| [`04_Generator_Metrics_Reference_Based.ipynb`](../../courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb) | Answer correctness via `GEval` — `criteria` and `evaluation_steps` forms — and semantic similarity | key |
| [`05_RAG_Eval_Inside_the_Pipeline.ipynb`](../../courses/01-rag-agent-tool-evaluation/05_RAG_Eval_Inside_the_Pipeline.ipynb) | Evaluation as LangGraph nodes — gates inside the pipeline, not scoring after it | none (mocked), key (real) |
| [`06_RAGAS_in_Practice.ipynb`](../../courses/01-rag-agent-tool-evaluation/06_RAGAS_in_Practice.ipynb) | RAGAS as a second opinion on the same case, and the pytest / CI pattern | key |
| [`07_RAG_Capstone_Build_and_Evaluate.ipynb`](../../courses/01-rag-agent-tool-evaluation/07_RAG_Capstone_Build_and_Evaluate.ipynb) | Build a RAG system, synthesise a golden set, run the whole suite | key |
| [Field guide, Part 1](../concepts/rag-agent-tool-evaluation.md) | **The companion to this whole level**, §1.1–§1.9 — one section per notebook above, plus the two with no notebook of their own: §1.5 writing a rubric that does not produce a vague judge, and §1.9 reading the results. §1.8 golden datasets is revisited properly at Level 3 | none |
| [Field guide Part 6, §6.1–6.3](../concepts/rag-agent-tool-evaluation.md) | The slow narrative behind labs 01–03, against the same numbers | none |

## Level 2 · Agents (tools, conversations, trajectories, outcomes)

| Read / run | Teaches | Cost |
|---|---|---|
| [`09_Tool_Use_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb) + [lab 04](../interactive-labs/04-tool-use-evaluation.html) | `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ToolUseMetric`. Five broken traces all score 1.00 until `should_exact_match=True`, then 0.17 | key |
| [`10_Task_Completion_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb) | `TaskCompletionMetric`, custom rubrics, outcome verification | key |
| [`08_MultiTurn_Conversational_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb) | `ConversationalGEval`, turn relevancy, knowledge retention, simulated conversations | key |
| [`12_Agent_Trajectory_Evaluation.ipynb`](../../courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb) + [lab 05](../interactive-labs/05-agent-trajectory-evaluation.html) | The nine trace-level checks on a refund agent. Five of nine never move; task success passes on 40 % waste | none (Parts A–B), key (Part C) |
| [Field guide Parts 2–3](../concepts/rag-agent-tool-evaluation.md) | §2.1 why per-turn rates multiply · §2.2 strict vs loose matching · §2.4 the polite tool failure · §3.2 the three trajectory traps | none |
| [Databricks ref, Part 4 — `p ** n`](../concepts/databricks-mlflow-evals.md) | At 95 % per turn a conversation is more likely failed than not by turn 14 | none |
| [`labs/multiturn-and-tool-eval/`](../../labs/multiturn-and-tool-eval/) *(optional)* | The same multi-turn and tool metrics twice — DeepEval and MLflow — side by side. Its own `uv` project | key |

## Level 3 · Ground truth

| Read / run | Teaches | Cost |
|---|---|---|
| [`03_the_golden_set.ipynb`](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb) | Case anatomy — six expectations, not one · strata by language and intent · the 20 % refusal quota · the datasheet. *Everything downstream is an opinion about this file* | none |
| [`04_eval_datasets_from_traces.ipynb`](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb) | Mining production traces: novelty-targeting over random sampling, threshold over top-k, provenance (`AssessmentSource`), merge by input hash. Mining gives inputs, not labels | key |
| [Field guide §1.8](../concepts/rag-agent-tool-evaluation.md) | Golden datasets — what to synthesise and what must be authored | none |
| [Question bank Part 3](../interview-prep/QUESTION_BANK.md) | Q10 day one → month three · Q11 eval set and traffic diverging · Q12 how big · Q13 who writes the labels | none |

## Level 4 · Judges, and the humans who validate them

| Read / run | Teaches | Cost |
|---|---|---|
| [`08_building_custom_judges.ipynb`](../../courses/03-agentic-eval-harness/08_building_custom_judges.ipynb) | `GEval` vs `DAGMetric` vs rubrics · position bias and same-model bias, measured · the verbosity audit and length-controlled probe | cached |
| [`09_human_feedback_and_calibration.ipynb`](../../courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb) | Three kinds of human feedback · Cohen's kappa by hand · the rubber-stamp signal · blinded preference testing | none |
| [`03_custom_scorers_and_judges.ipynb`](../../courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb) | `@scorer`, `make_judge`, the trace-based judge (`{{ trace }}`) — judging *how* the agent worked | key |
| [`07_judge_alignment_memalign.ipynb`](../../courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb) | Aligning a judge to expert labels; measuring agreement, never average score; why a falling score is success | workspace |
| [Field guide §0.3](../concepts/rag-agent-tool-evaluation.md) | LLM-as-judge failure modes | none |
| [Tutorial §4](../guide-audits/openai-eval-guide-tutorial.md) | Code vs judge vs human · the three judge biases · kappa · blinded preference, in 3–4 lines each with a TODO | none |
| [Question bank Part 4](../interview-prep/QUESTION_BANK.md) | Q14 why believe the number · Q15 20 % disagreement · Q16 when not to use a judge · Q17 judge says 0.9, customer says terrible | none |

## Level 5 · Statistics and stratified reporting

| Read / run | Teaches | Cost |
|---|---|---|
| [`10_stratified_reporting_and_statistics.ipynb`](../../courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb) | Sample size · McNemar for paired runs · the bootstrap in ten lines of stdlib · the small-stratum rule | none |
| [`stratified-reporting-explained.html`](../interview-prep/stratified-reporting-explained.html) | One table: overall 87.5 % → 90 % while Hindi collapses 88 % → 50 % | none |
| [Online vs offline §5](../concepts/online_vs_offline_evaluation.md) | The sampling-resolution problem; §5.1 in plain English | none |
| [Databricks ref, Part 4 — the numbers](../concepts/databricks-mlflow-evals.md) | Wilson intervals: ±0.045 at 100 traces, ±0.018 at 600. A two-point drop needs ~606 scored traces — 30 % of 2,000/day, not 5 % | none |
| [Question bank Q4, Q21](../interview-prep/QUESTION_BANK.md) | "One number for a dashboard" · "a metric dropped two points" | none |

## Level 6 · The release gate and CI

| Read / run | Teaches | Cost |
|---|---|---|
| [`11_the_release_gate_and_ci.ipynb`](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) | Four checks in order — safety, aggregate floor, per-stratum floor, cost ceiling — and four scenarios | none |
| [`ci/apply_gate.py`](../../courses/03-agentic-eval-harness/ci/apply_gate.py) + [`release-gate.yml`](../../.github/workflows/release-gate.yml) | The free, stdlib-only decision layer, and why the paid `evaluate` job is *not* on the merge path | none |
| [`05_prompt_versioning_and_regression.ipynb`](../../courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb) | Registering ≠ deploying · alias as rollback · the two-condition gate · tolerance 0.00 deterministic, 0.02 judged | key |
| [`08_automated_improvement_gepa.ipynb`](../../courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb) | An optimised prompt passes the *same* gate, scored on a superset of what it optimised | workspace |
| [`launch-gate.html`](../concepts/launch-gate.html) | The gate on one page | none |
| [Question bank Part 6, Case 13, Case 14](../interview-prep/QUESTION_BANK.md) | Safe to ship · the optimiser's higher score · a green dashboard that is wrong · Case 13 designs the CI gate | none |

## Level 7 · Online evaluation and the loop

| Read / run | Teaches | Cost |
|---|---|---|
| [`12_online_evaluation_and_the_loop.ipynb`](../../courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb) | Reference-free metrics · five alerts · incident drills · the canary · the label queue that closes the loop | none |
| [`06_online_eval_production_monitoring.ipynb`](../../courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb) | Traces as tables · sampled live scorers · register *and* start · the mechanical online-eligibility test | workspace |
| [Online vs offline](../concepts/online_vs_offline_evaluation.md) | The two regimes, what flows between them, where human alignment fits | none |
| [Field guide Part 4](../concepts/rag-agent-tool-evaluation.md) | §4.1 what can never go online · §4.2 sampling and alerting · §4.3 what tracing adds | none |
| [`13_Production_Grade_Agent_Eval_Overview.ipynb`](../../courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb) → [Arize labs](../../labs/agent-evaluation/arize-phoenix-labs/) *(optional)* | Live tracing plus offline experiments in Phoenix — the one framework built around traces rather than test cases | key + Phoenix |
| [`rag-vs-support-eval-walkthrough.html`](../concepts/rag-vs-support-eval-walkthrough.html) | Offline, online and the gate walked through on two real systems | none |
| [Question bank Part 5, Case 15](../interview-prep/QUESTION_BANK.md) | Q18 offline vs online · Q19 what to sample · Q20 beyond a quality score · Case 15 sets up monitoring | none |

## Level 8 · Safety, adversarial, and multi-agent attribution

| Read / run | Teaches | Cost |
|---|---|---|
| [`07_safety_and_policy_checks.ipynb`](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb) | Assertions that block absolutely and are never averaged · why a flaky safety test is a safety problem | cached |
| [`06_agent_handoff_and_end_to_end.ipynb`](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb) | Routing confusion matrix · handoff integrity · circular-handoff detection · trajectory matching · the SQLite final-state check · blame attribution | key |
| [`10_capstone_edge_cases_and_crossref.ipynb`](../../courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb) | Design by attack surface: classes × variants · behavioural boundaries · channel confusion · the polite tool failure · stating N/A with a reason | key |
| [`09_multiturn_and_tool_selection.ipynb`](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) | Consent lives between turns · three approval outcomes · gate by prompt, verify by evaluation · gates that must report *not measured*, never 0 | key |
| [`eval-harness-two-usecases.html`](../concepts/eval-harness-two-usecases.html) | The same harness on an enterprise RAG agent and on a tool-calling multi-agent system, side by side | none |
| [Field guide Part 5](../concepts/rag-agent-tool-evaluation.md) | Handoff quality, nested traces, attribution | none |
| [Question bank Part 8, Cases 8, 16, 17](../interview-prep/QUESTION_BANK.md) | Adversarial sets worth having · evidence for legal · "we tested 15 jailbreak strings and passed 12" · "the agent must never do X" | none |

## Level 9 · The harness as a product

| Read / run | Teaches | Cost |
|---|---|---|
| [Course 03 README — *Cost*, *Judge verdicts are cached*, *Fault switches*](../../courses/03-agentic-eval-harness/README.md) | The judge runs on a different model than the agent (`gpt-4.1-mini`, 6 of 6 calls at ~2.5 s vs a 248 s runaway) · `SCORE_MODE` auto / strict / record · a cache that exists for comparability, not savings · twelve faults that all return a fluent 200 | none |
| [Course 03 README — *Conventions*](../../courses/03-agentic-eval-harness/README.md) | No shared modules, files in `data/` as the handoff, no pandas — every number traceable from the notebook that produced it | none |
| [`00_eval_strategy_worksheet.ipynb`](../../courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb) | Thresholds and blocking flags written before the agent exists — eval-driven development as a worksheet | none |
| [`genai-eval-playbook-coverage-map.md`](../guide-audits/genai-eval-playbook-coverage-map.md) | What this repo does *not* build: acceptance criteria with sign-off owners, stakeholder dashboards, the staged canary ladder, retrieval operations. Thirteen open gaps, clustered | none |
| [`fde-playbook-end-to-end-evaluation.html`](../interview-prep/fde-playbook-end-to-end-evaluation.html) | The customer-facing version of the whole pipeline: dataset sizes by stage, the canary ladder with rollback triggers, four dashboard views | none |
| [Question bank Part 9, Cases 18, 19](../interview-prep/QUESTION_BANK.md) | Q33 cost · Q34 ownership · Q35 is the eval system still working · Case 18 build the platform · Case 19 cost is 4× | none |

---

## OpenAI round — follow-up mapping

| Follow-up | The answer lives in |
|---|---|
| **"You have no labelled data. What do you ship in week one?"** | Referenceless checks first — faithfulness, relevancy, safety, deterministic assertions ([field guide §1.3, §0.2](../concepts/rag-agent-tool-evaluation.md); [course 03 nb 07](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb)). Log everything and mine later ([course 02 nb 01](../../courses/02-databricks-mlflow-evals/01_minimal_agent_and_tracing.ipynb) → [nb 04](../../courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb)). A small stratified golden set with a refusal quota before the first judge ([course 03 nb 03](../../courses/03-agentic-eval-harness/03_the_golden_set.ipynb)). Spoken form: [Q10](../interview-prep/QUESTION_BANK.md), [Q7](../interview-prep/QUESTION_BANK.md) |
| **"What's the smallest thing you could launch that produces a measurable business number?"** | Rollout by risk tier — assistive → gated-write → autonomous — not by calendar (Spine step 7; [Case 3](../interview-prep/QUESTION_BANK.md)). End-state verification as the business number where a side effect exists ([§0.3 of the bank](../interview-prep/QUESTION_BANK.md); [course 03 nb 06](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb)). What to challenge when the ask is "launch next week": [Q32](../interview-prep/QUESTION_BANK.md), [Q4](../interview-prep/QUESTION_BANK.md) |

## OpenAI round — vocabulary mapping

| OpenAI term | The evaluation you already know |
|---|---|
| `Handoff` | Routing confusion matrix, handoff integrity, circular-handoff detection, blame attribution — [course 03 nb 06](../../courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb); [field guide Part 5](../concepts/rag-agent-tool-evaluation.md) |
| `Guardrail` | Assertions that block and are never averaged — [course 03 nb 07](../../courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb); approval gating tested rather than assumed — [course 02 nb 09](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) |
| `Session` / multi-turn | Session-level vs turn-level, context retention, `p ** n` — [course 01 nb 08](../../courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb); [course 02 nb 09](../../courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb) |
| Built-in **file search** | Retrieval metrics with and without labels — Level 1 |
| Function tools | Tool selection vs argument correctness, strict vs loose — [course 01 nb 09](../../courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb); [course 03 nb 05](../../courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb) |
| Structured outputs | Deterministic scorers over a parseable output — the cheapest rung of the cost ladder ([field guide §0.4](../concepts/rag-agent-tool-evaluation.md)) |
| Evals as a product surface | A gate that returns *ship / don't ship*, wired to CI — [course 03 nb 11](../../courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb) |

---

## Databricks — phase-by-phase notebook mapping

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

## Databricks — the same idea in three vocabularies

| RAGAS / DeepEval | MLflow | Asks |
|---|---|---|
| Contextual relevancy / context precision | `RetrievalRelevance` | Is each retrieved chunk relevant? |
| Context recall | `RetrievalSufficiency` | Do the chunks contain everything the answer needs? |
| Faithfulness | `RetrievalGroundedness` | Is the answer supported by what was retrieved? |
| Answer relevancy | `RelevanceToQuery` | Does the answer address the question? |
| Answer correctness | `Correctness` | Is it right against a reference? |
