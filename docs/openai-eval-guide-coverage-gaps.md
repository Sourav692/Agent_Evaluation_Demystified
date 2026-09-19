# OpenAI "Evaluation Best Practices" — Repo Coverage

Maps every topic in OpenAI's [Evaluation best practices guide](https://developers.openai.com/api/docs/guides/evaluation-best-practices?api-mode=responses)
to where this repo teaches it, and names what is genuinely missing.

**Checked against disk 2026-09-20; every row verified per course rather than repo-wide.**
Every path below was verified to exist. **All paths are relative to the repository root**,
not to this file. Verdicts rest on the 107 tracked files under `courses/`, `docs/` and
`labs/`; `labs/agent-evaluation/arize-phoenix-labs/` is third-party and `archive/` is
superseded, so neither counts as coverage.

**The headline, as of 2026-09-20: the measurement surface is essentially complete, and the
four open rows are one framework and three techniques.** The repo taught the *concepts*
thoroughly from the start — golden datasets, groundedness, tool and trajectory evaluation,
safety taxonomies, release gating and the online loop. What was thin was narrower than it
looked. **Scoping per course is what made the real gaps visible:** circular handoffs read as
"n/a" repo-wide because course 02 has one agent, while course 03's supervisor graph made it a
live hole — closed 2026-09-20. The same scoping showed course 02 has no judge-bias probe at
all, which its own cross-reference claims it does.

|                                                            | Count |
| ---------------------------------------------------------- | ----- |
| ✅ Covered                                                  | 42    |
| 🟡 Partial — concept present, one dimension missing        | 5     |
| ⏭️ Descoped — deliberately not building                    | 4     |
| ❌ Gap                                                      | 4     |

*(55 rows, counted by badge across §1–§7 — 12 · 8 · 9 · 11 · 12 · 2 · 1. One row flipped from
❌ to ✅ on 2026-09-20 when the loop check was built, and the tally was recounted rather than
decremented.)*

---

## 1. What Are Evals?

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Eval-driven development | `courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb` — thresholds written before a single score existed. `courses/03-agentic-eval-harness/03_the_golden_set.ipynb` does the same for the harness | ✅ Covered |
| Task-specific over generic assessments | `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §4, the code-first scorer decision; `courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb` exists because no built-in scorer knows the agent's design | ✅ Covered |
| Log everything; mine eval cases later | `courses/02-databricks-mlflow-evals/01_minimal_agent_and_tracing.ipynb` then `04_eval_datasets_from_traces.ipynb` — novelty-targeted mining, and the repo's only holdout set | ✅ Covered |
| Automate scoring where feasible | `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` — deterministic assertions first, judges only where judgement is needed | ✅ Covered |
| Treat evaluation as continuous | `courses/02-databricks-mlflow-evals/06_online_eval_production_monitoring.ipynb`, `courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb` | ✅ Covered |
| Maintain agreement with human feedback | `courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb` (MemAlign), `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` (Cohen's and weighted kappa) | ✅ Covered |
| **Anti-pattern:** overly generic metrics | `courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb` `EVAL_DIMENSIONS`; custom scorers in phase 3 | ✅ Covered |
| **Anti-pattern:** biased dataset design | `courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb` — hand-written sets are structurally blind; `courses/03-agentic-eval-harness/03_the_golden_set.ipynb` adds strata and a datasheet | ✅ Covered |
| **Anti-pattern:** vibe-based evaluation | `courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb` returns a ship/no-ship decision, not a number | ✅ Covered |
| **Anti-pattern:** neglecting human feedback | Both alignment notebooks measure *agreement*, never average score | ✅ Covered |
| Industry benchmarks (MMLU, HuggingFace leaderboard) | ⏭️ **Descoped 2026-09-20 — not building this.** One passing MMLU mention in `courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb`; zero occurrences of `leaderboard`. This repo is about application-specific evaluation, and the guide itself frames benchmarks as the thing you move past. A paragraph saying why would be the whole of it | ⏭️ Descoped |
| Standard numerical scores — ROUGE, BERTScore; **anti-pattern:** BLEU, perplexity | ❌ **Zero occurrences of `ROUGE`, `BLEU`, `BERTScore` or `perplexity` across all 186 tracked files** — not as technique and not as critique. The guide gates its worked summarisation example on **ROUGE-L ≥ 0.40** and names BLEU as an anti-pattern, so a reader of this repo cannot answer *"why don't you use ROUGE?"*. Belongs in `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §1 as the n-gram-overlap branch | ❌ Gap |

## 2. Design Your Eval Process

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Step 1 — define the eval objective | `courses/02-databricks-mlflow-evals/00_eval_strategy_worksheet.ipynb` is a worked answer to exactly this | ✅ Covered |
| Step 2 — collect a dataset | `courses/03-agentic-eval-harness/03_the_golden_set.ipynb` — 40 cases, strata, datasheet, `content_hash`, version | ✅ Covered |
| Data sources: production, domain-expert, synthetic, historical | All four present — `courses/02-databricks-mlflow-evals/04_eval_datasets_from_traces.ipynb`, `labs/rag-evaluation/4.End_to_End_RAG_System_Evaluation.ipynb` | ✅ Covered |
| Data source: purchased datasets | ⏭️ **Descoped.** Listed by the guide as one of six sources. There is nothing to teach beyond the sentence, and no fictional-corpus equivalent | ⏭️ Descoped |
| Step 3 — define eval metrics | The bulk of all three courses | ✅ Covered |
| Step 4 — run and compare evals | `courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb` — paired comparison, McNemar's test, bootstrap CIs; `courses/02-databricks-mlflow-evals/05_prompt_versioning_and_regression.ipynb` builds the v1-vs-v2 regression deliberately | ✅ Covered |
| Step 5 — continuous evaluation | `courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb` closes the loop back into notebook 03 | ✅ Covered |
| *"LLMs discriminate better than they generate"* — prefer pairwise, classification and scoring over open-ended | 🟡 **Applied, never stated.** `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 5 uses `ArenaGEval` pairwise; `07_safety_and_policy_checks.ipynb` uses `DAGMetric` decision trees, which is forced classification. Neither says *why that shape*. As written a reader can reproduce these judges but cannot derive the shape of a new one. One paragraph in `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §4, beside the existing code-vs-judge decision, converts three worked examples into a transferable rule | 🟡 Partial |

## 3. Identify Where You Need Evals

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Single-turn model interactions | `courses/01-rag-agent-tool-evaluation/01`–`07`, `courses/02-databricks-mlflow-evals/02_offline_eval_fundamentals.ipynb` | ✅ Covered |
| Workflow architectures (multistep chains) | `courses/02-databricks-mlflow-evals/03_custom_scorers_and_judges.ipynb` — the trajectory judge | ✅ Covered |
| Single-agent architectures | `courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb`, `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` | ✅ Covered |
| Multi-agent architectures | `courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb` — supervisor plus specialists | ✅ Covered |
| Instruction following | Covered as **policy assertions** — `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` Part 1, four policies written as functions. *(Named in the guide's vocabulary only in `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb`; see the terminology table below)* | ✅ Covered |
| Functional correctness | Covered as **task completion** and the **final-state check** — `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb`, `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` Part 5, which verifies the refund was written exactly once against SQLite | ✅ Covered |
| Tool selection | `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` Part 2, DeepEval `ToolCorrectnessMetric` | ✅ Covered |
| Data precision | Covered as **argument correctness** — `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` §2.1, `ArgumentCorrectnessMetric` | ✅ Covered |
| Agent handoff accuracy | `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` — routing as classification with a confusion matrix, a confidence-threshold sweep, and handoff-payload integrity. **Course 02 is n/a here: one agent, no handoffs**, and its own map correctly says so. *(That map also says "Not covered", which was true of course 02 and false of the repo once course 03 existed)* | ✅ Covered |

## 4. Create and Combine Different Types of Evaluators

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Metric-based: exact match, string match, function-call accuracy, executable evals | `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb`, `07_safety_and_policy_checks.ipynb`, and the executable case in `06_agent_handoff_and_end_to_end.ipynb` Part 5 | ✅ Covered |
| Human evals: numerical grading, pass/fail plus score | `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` labelling panel; `courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb` Likert scales | ✅ Covered |
| Human evals: consensus votes, multiple rounds of review | 🟡 **Left as an exercise.** `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` names the need — *"`labeller` — because inter-annotator agreement needs at least two of them"* — then defers it to *"Exercise 2"*. The built path runs one labeller, while Cohen's and weighted kappa are taught as core in the same notebook. **Course 02 is worse:** phase 7 measures agreement against a single rater with no exercise offered | 🟡 Partial |
| Human evals: randomized blinded testing, ranking | ❌ **Self-declared missing.** `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb`: *"Phase 7 collects expert ratings and measures agreement, but does not run A/B preference studies with multiple raters and consensus."* Still true of course 03. Nearly free once consensus above is built — blinding and randomising an existing two-rater comparison is a presentation change | ❌ Gap |
| LLM-as-judge: pairwise, single-answer, reference-guided | All three — `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` compares `GEval`, `DAGMetric` and RAGAS rubrics on one job; `courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb` is the reference-guided case | ✅ Covered |
| **Position bias** | `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 5 — a runnable probe that scores a pair in both orders and counts verdict flips. **Course 02 has no bias probe of any kind:** zero occurrences of `position bias` across its 23 files, and the word "bias" there only ever means *dataset* bias. *(Its cross-reference claims "LLM-as-judge, incl. bias caveats — Phases 2, 3, 7". Phase 7 aligns the judge against human labels, which is a different check — see the corrections section)* | 🟡 Partial |
| **Verbosity bias**; "control for response length" | ❌ **Stated once, never probed.** `docs/interview-prep/QUESTION_BANK.md` line 2962: *"Longer answers win pairwise comparisons at a rate unrelated to quality, so a win rate reported without a length distribution is partly measuring verbosity."* No notebook probes it and no judge controls for length. Matters because the canary in `courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb` compares a new build against the shipped one — if the new build is chattier, part of the win is word count. Part 5 of notebook 08 is a working template to clone. *(Not the same as `courses/02-databricks-mlflow-evals/scorers.py` line 306 `ResponseLengthScorer`, which scores the agent's verbosity as a quality dimension)* | ❌ Gap |
| Clear rubrics; reformat to multiple choice where possible | `DAGMetric` decision trees in `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` and `08_building_custom_judges.ipynb` are exactly this | ✅ Covered |
| Scale only after consistency with human annotations | `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` §2.1 — using labels to *set* a threshold rather than guess it | ✅ Covered |
| Use the most capable model first, then optimise down | 🟡 **Inverted here, deliberately.** All judges are pinned small — `gpt-4o-mini` in courses 01 and 02, `gpt-4.1-mini` in course 03. The course 03 pin is load-bearing: `gpt-4o-mini` fell into repetition loops (`courses/03-agentic-eval-harness/README.md` line 149). The guide's ordering is never discussed | 🟡 Partial |
| **Same-model bias** | ➕ **Beyond the guide.** `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 6 — `gpt-4o-mini` judging `gpt-4o-mini` rates itself high. The guide names position and verbosity bias but not this one | ✅ Covered |

## 5. Handle Edge Cases

The guide's eleven-item list is tracked in code at `courses/02-databricks-mlflow-evals/edge_cases.py`,
in the `OPENAI_EDGE_CASE_COVERAGE` dict. Every verdict there was re-verified 2026-09-20.

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Non-English / multilingual content | `courses/03-agentic-eval-harness/03_the_golden_set.ipynb` stratifies en/es/hi with Hindi deliberately thin; `courses/02-databricks-mlflow-evals/` phase 10 `non_english` | ✅ Covered |
| Diverse formats (XML, JSON, Markdown, CSV) | Phase 10 `format_variability` — JSON embedded in a question | ✅ Covered |
| Multiple input modalities | ⏭️ **Descoped.** All three courses are text-only. Audio and image inputs need a different agent, not a different evaluation technique — listed so the omission is deliberate rather than silent | ⏭️ Descoped |
| Multiple intents in a single request | Phase 10 `multiple_intents`; `multi_intent` is a gated stratum in `courses/03-agentic-eval-harness/11_the_release_gate_and_ci.ipynb` | ✅ Covered |
| Typos and minimal context | Phase 10 `minimal_context`; phase 4's traffic mix includes typo variants | ✅ Covered |
| Long conversation histories | 🟡 `courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb` covers 2–3 turns and the `p**n` arithmetic. Context-window pressure at 20+ turns is untested. **Course 03 does not cover multi-turn at all** — only 2 of its 18 files mention it | 🟡 Partial |
| Ambiguous tool response properties | Phase 10 `ambiguous_tool_response` — both read tools' `{"found": false}` paths, the polite failure that is easy to skate past | ✅ Covered |
| **Circular agent handoffs** | **Closed 2026-09-20.** `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` §2.1 adds two free checks over the trajectory — a revisited agent (`billing → knowledge → billing`) and a `MAX_HOPS = 3` bound — with both halves proven against synthetics, because all 25 recorded trajectories are single-agent and a zero from an unproven detector is not evidence. The section also shows handoff integrity *passing* the looping run, which is why it is a separate check. `loops_flagged` and `max_hops_seen` now land in `data/agent_report.json`. *(Was `n/a` in course 02's map — correct there, one agent; that verdict went stale repo-wide when course 03's supervisor graph was built)* | ✅ Covered |
| Multiple tool calls | `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` — repeated-call detection, strict vs flexible ordering | ✅ Covered |
| Jailbreak attempt resistance | `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb` — 5 attack classes × 3 variants, designed by attack surface rather than by example; `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` | ✅ Covered |
| Custom formatting preferences | Phase 10 `prompt_conflict` — a customer demanding a one-word answer against a policy that requires a citation | ✅ Covered |
| System / user prompt conflict resolution | Phase 10 `instruction_override` and `authority_impersonation` classes | ✅ Covered |

## 6. Use Evals to Improve Performance

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| Eval insight → improvement flywheel | `courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb` (GEPA, gated by phase 5); `courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb` Part 6 feeds sampled production traces back into notebook 09 for labels and notebook 03 for new goldens | ✅ Covered |
| Reinforcement fine-tuning as the data flywheel | ⏭️ **Descoped, and declared.** `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb`: *"Phase 8 optimises the prompt. Reinforcement fine-tuning from eval signal is the next rung and is out of scope."* The improvement lever here is the prompt | ⏭️ Descoped |

## 7. Platform Surface

| Guide topic | Repo coverage | Status |
| --- | --- | --- |
| **Evals API and the Graders tool** | ❌ **Zero occurrences of `Evals API`, `openai.evals`, `client.evals` or `grader`** anywhere in live material. The repo's stated pitch is "deliberately the same ideas in four frameworks" — DeepEval, RAGAS, MLflow 3 GenAI and Arize Phoenix — and the platform this guide is written around is the one framework not represented. Belongs in a new lab under `labs/`, beside `labs/llm-as-judge/`, not inside a numbered course: the courses are sequential and this is a parallel framework, not a next step | ❌ Gap |

---

## The gap list

Five rows have been tracked as gaps. One is built; four remain open.

| Gap | Outcome |
| --- | --- |
| Circular agent handoffs | **Built** 2026-09-20 — `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` §2.1 *(uncommitted; the three new cells carry no outputs because the notebook has not been re-executed)* |
| Verbosity-bias probe | **Open** — one section in `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb`, cloning the position-bias probe beside it |
| Blinded / randomized preference testing | **Open** — follows almost free from multi-rater consensus in `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` |
| ROUGE / BLEU / BERTScore | **Open** — one section in `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §1 |
| OpenAI Evals API and Graders | **Open** — a new lab, not a course section |

## When a gap is worth closing

Four rows were descoped rather than built. The test that separated them from the four gaps:

> **Close it when the guide's version tests something your system can actually do wrong.
> Descope it when your system makes the failure unreachable, or when it is a different
> spelling of a check you already run.**

- **Circular handoffs** — passed, and was the clearest case in the document. Course 03 owns
  the supervisor graph that makes the failure reachable, so "untested" was a real hole rather
  than an inapplicable row. Every other gap needed new apparatus; this needed a test.
- **Multimodal, purchased datasets, reinforcement fine-tuning** — descoped because the
  systems are text-only, the source has nothing to teach, and the improvement lever here is
  the prompt. All three were already declared in course 02's own "what this track does not
  cover" list, which is the right place for them.
- **Industry benchmarks** — descoped on the weakest grounds of the four. It is not that the
  topic is inapplicable; it is that the guide itself treats benchmarks as what you move past,
  and this repo's whole subject is what replaces them.

**The scoping rule underneath all of this:** a verdict that averages two courses hides
whichever one is weaker. Circular handoffs read `n/a` repo-wide because course 02 has one
agent; course 02's missing bias probe read 🟡 repo-wide because course 03 has two. Neither is
visible without splitting the scope.

## Claims in course 02's own map that no longer hold

`courses/02-databricks-mlflow-evals/` carries the repo's only other cross-reference to this
guide — the `OPENAI_EDGE_CASE_COVERAGE` dict in `edge_cases.py`, and the mapping table in
`10_capstone_edge_cases_and_crossref.ipynb`. Both say *"this track"* and mean course 02 alone.

| Claim | Recorded | Today |
| --- | --- | --- |
| *"Circular agent handoffs — n/a. Single agent, no handoffs. Would require the multi-agent supervisor pattern"* | `n/a` | **Superseded.** Course 03 *is* that pattern, and the check was built 2026-09-20 |
| *"LLM-as-judge, incl. bias caveats — Phases 2, 3, 7"* | Covered | **Overstated.** Course 02 has no bias probe; phase 7 measures human agreement, which is a different check |
| *"Multi-agent handoff accuracy — Not covered"* | Not covered | **Resolved elsewhere.** `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` covers routing accuracy and handoff integrity |

The remaining nine edge-case verdicts were re-verified and hold.

## Terminology mapping

Covered in substance, named differently. A liability for interview preparation, where the
interviewer uses the guide's words rather than this repo's.

| The guide says | This repo says | Where |
| --- | --- | --- |
| Data precision | Argument correctness | `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` §2.1 |
| Instruction following | Policy assertions | `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` Part 1 |
| Functional correctness | Task completion; final-state check | `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb`; `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` Part 5 |
| Reference-guided grading | Reference-based metrics | `courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb` |

Two run the other way — covered here, absent from the guide: **same-model bias**
(`courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 6) and **stratified
reporting with a detection limit** (`courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb`).

## Related

[`genai-eval-playbook-coverage-map.md`](genai-eval-playbook-coverage-map.md) (beside this
file) is the same exercise against *LLM Evaluation for GenAI Forward Deployed Engineers*, a
customer-facing playbook. It finds fourteen gaps clustered around commercial apparatus —
acceptance criteria, sign-off owners, stakeholder dashboards, staged rollout — and retrieval
operations. **This document is the measurement audit; that one is the deployment audit.**
The two overlap in exactly one item: ROUGE / BLEU / BERTScore, ❌ here and P-12 there.

[`concepts/openai-evaluation-guide-plain-english.md`](concepts/openai-evaluation-guide-plain-english.md)
is the teaching companion — the same guide in plain language with one worked example running
through it. **This document is the audit; that one is the lesson.** Keep them in step: if a
row here changes status, the matching section there changes too.

## What actually moves the needle

Closing all four remaining rows would not change what this repo teaches nearly as much as two
cheaper things:

- **Fix the course 02 cross-reference** (~20 minutes). It is the repo's own map of this guide,
  it is the first thing a reader trusts, and three of its claims are wrong — one stale, one
  overstated, one resolved elsewhere. A wrong map costs more than a missing section.
- **Learn the four renamings** in the terminology table. The substance is all there; only the
  guide's nouns are missing, and an interviewer will use theirs.
- If there is build time after that, **verbosity bias** is the highest-value gap — the
  template is already in the notebook next door, and the canary comparison in notebook 12 is
  currently measuring word count as part of quality without saying so.
