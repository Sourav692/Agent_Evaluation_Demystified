# OpenAI Evaluation-Guide Coverage Gaps

> An audit of this repository against OpenAI's
> [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices?api-mode=responses)
> guide, performed 2026-09-19 and re-verified the same day against the restored course 02
> notebooks. Every section of the guide was mapped to the material that
> implements it. **This document records only what is missing, partial, stale or renamed** —
> the positive mapping already lives in the repo, and §2 says where.

---

## 1. Scope and method

Every heading, metric, grader type, architecture pattern and anti-pattern in the guide was
extracted, then searched across the tracked source of this repository. Keyword hits were
opened and read rather than counted, because several guide concepts are covered here under a
different name and two are named without being implemented.

| Set | Files | Role in this audit |
|---|---|---|
| All tracked `.ipynb` / `.md` / `.py` | 199 | The starting set |
| Minus `labs/agent-evaluation/arize-phoenix-labs/` | 186 | Third-party material, kept verbatim, not this repo's claim |
| **Live material** — `courses/`, `docs/`, `labs/` | **107** | **Coverage verdicts are based on these** |
| `archive/` | 24 | Superseded. Hits noted, never counted as coverage |

Four verdicts are used:

| Verdict | Meaning |
|---|---|
| **Gap** | Neither the technique nor a renamed equivalent appears anywhere in live material |
| **Partial** | Present as prose, as a reader exercise, or in one direction only |
| **Stale** | Recorded in the repo's own coverage map, but the verdict no longer matches the repo |
| **Renamed** | Fully covered under different terminology — see §6, not counted as a gap |

**Headline:** of the guide's roughly forty distinct recommendations, anti-patterns, evaluator
types and edge cases, the repository covers the large majority outright. Eight are open, and
one previously recorded verdict has gone stale.

> **A note on course 02.** Its eleven notebooks were round-tripped through a Databricks
> workspace and converted back to `.ipynb` on the audit date, so they carry uncommitted
> workspace edits: added `%pip install` cells, `load_dotenv()` in the setup cells, a
> `MLFLOW_TRACKING_MODE` default of `"databricks"` in notebook 09, and real catalog, schema and
> SQL-warehouse values where notebooks 07 and 08 previously had `<YOUR_CATALOG>` placeholders.
> None of it changes a verdict below — every finding was re-verified against the restored
> notebooks — but the line numbers cited here were confirmed after that round trip, not before.

---

## 2. What is already mapped

Two places in the repo already cross-reference this guide. Both were written before
`courses/03-agentic-eval-harness/` existed, and both are scoped to course 02 alone.

| Where | What it holds |
|---|---|
| `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb` | Section "The whole track, against OpenAI's evaluation guide" — a recommendation-by-recommendation table, plus an explicit "What this track does not cover" list |
| `courses/02-databricks-mlflow-evals/edge_cases.py`, line 274 | `OPENAI_EDGE_CASE_COVERAGE` — the guide's 11-item edge-case list as a dict of `covered` / `partial` / `n/a` verdicts, each with a justification |

**Their limitation.** Both say "this track" and mean course 02. A reader of that notebook is
told *"Multi-agent: handoff accuracy — Not covered"*, which is true of course 02 and false of
the repository: `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` covers
exactly that. The map did not rot — the repo grew past it.

---

## 3. The gaps at a glance

Ordered by what closing them costs against what they are worth, not by the guide's order.

| ID | Gap | Verdict | Severity | Where the fix belongs |
|---|---|---|---|---|
| **G1** | Circular agent handoffs are never tested | Gap | **High** | `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` |
| **G2** | Verbosity bias is stated but never probed | Partial | Medium | `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` |
| **G3** | Multi-rater consensus is a reader exercise | Partial | Medium | `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` |
| **G4** | OpenAI Evals API and Graders tool absent | Gap | Medium | A new lab under `labs/` |
| **G5** | ROUGE / BLEU / BERTScore absent, as technique and as critique | Gap | Medium | `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` |
| **G6** | Blinded, randomized preference testing | Gap | Low–Medium | Same notebook as G3 |
| **G7** | Industry benchmarks not discussed | Gap | Low | `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` |
| **G8** | The discrimination principle is applied, never stated | Partial | Low | `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` |

---

## 4. The gaps in detail

Each entry carries the same four fields: what the guide asks for, what was found, where a fix
belongs, and why it is worth doing.

### G1 — Circular agent handoffs are never tested

**Guide item.** Edge cases → contextual complexity → "circular agent handoffs".

**Evidence.** Zero occurrences of `circular`, `recursion_limit`, `max_iterations`, `max_steps`
or any other loop guard in either
`courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb` or
`courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb`.

**Where the fix belongs.** `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb`.
The supervisor and specialist agents that make the failure reachable are built in
`courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb`.

**Why it matters.** This is the one gap where the repository already owns the system needed to
exercise it. Every other gap needs new apparatus; this needs a test. It is also recorded as
`n/a` in the existing coverage map on the grounds that there are no handoffs — which stopped
being true when course 03 was written. See §5.

### G2 — Verbosity bias is stated but never probed

**Guide item.** LLM-as-a-judge → challenges → "verbosity bias", and the paired recommendation
to "control for response length".

**Evidence.** The insight is written down once, in `docs/interview-prep/QUESTION_BANK.md`
line 2962: *"Longer answers win pairwise comparisons at a rate unrelated to quality, so a win
rate reported without a length distribution is partly measuring verbosity."* No notebook
probes it, and no judge in the repository controls for response length.

**Where the fix belongs.** `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb`,
beside Part 5. The position-bias probe there is a working template: it scores a pair in both
orders and counts verdict flips, and a length-controlled variant is the same shape.

**Why it matters.** The repo already probes two judge biases and teaches that a judge is the
thing under test. Verbosity is the third bias the guide names, and it is the one that silently
inflates the canary comparisons in
`courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb`.

> **Not the same thing.** `courses/02-databricks-mlflow-evals/scorers.py` line 306 defines
> `ResponseLengthScorer`, which scores *the agent's* verbosity as a quality dimension. That is
> a different concern from *a judge* preferring longer answers.

### G3 — Multi-rater consensus is a reader exercise

**Guide item.** Human evals → "consensus votes for aggregation", and multiple rounds of
detailed review.

**Evidence.** `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb` names
the need — *"`labeller` — because inter-annotator agreement needs at least two of them"* — and
then defers it: *"Exercise 2 — Add a second labeller and measure inter-annotator agreement."*
The path the notebook actually builds runs one labeller.

**Where the fix belongs.** The same notebook, promoting Exercise 2 into the built path.

**Why it matters.** Cohen's kappa and weighted kappa are taught as core material in that
notebook and in `courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb`. Both
statistics require two raters by definition, so the core lesson currently rests on an exercise
the reader may skip.

### G4 — The OpenAI Evals API and Graders tool are absent

**Guide item.** "Other resources" → the Evals API and the Graders tool. The guide's whole
worked flow assumes them.

**Evidence.** Zero occurrences of `Evals API`, `openai.evals`, `client.evals` or `grader`
anywhere in live material.

**Where the fix belongs.** A new lab under `labs/`, beside `labs/llm-as-judge/`, rather than
inside a numbered course — the courses are sequential and this is a parallel framework, not a
next step.

**Why it matters.** The repository's stated pitch is "deliberately the same ideas in four
frameworks" — DeepEval, RAGAS, MLflow 3 GenAI and Arize Phoenix. The platform this guide is
written around is the one framework not represented.

### G5 — ROUGE, BLEU and BERTScore are absent, as technique and as critique

**Guide item.** Two separate places. "What are evals?" lists ROUGE and BERTScore as standard
numerical scores; the anti-patterns list names perplexity and BLEU as overly generic. The
guide's worked summarisation example then gates on **ROUGE-L ≥ 0.40**.

**Evidence.** Zero occurrences of `ROUGE`, `BLEU`, `BERTScore` or `perplexity` across all 186
tracked files — not in the courses, not in the labs, not in the concept companions.

**Where the fix belongs.** `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb`
§1, as the n-gram-overlap branch of the taxonomy.

**Why it matters, twice over.** The guide uses ROUGE-L as a live threshold in one example and
names BLEU as an anti-pattern in another, so the repo covers neither the technique nor the
argument against it. A reader of this material cannot currently answer *"why don't you use
ROUGE?"* — which is the more likely question of the two.

### G6 — Blinded and randomized preference testing

**Guide item.** Human evals → "randomized blinded testing" and "ranking".

**Evidence.** Already self-declared in
`courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb`, under "What
this track does not cover": *"Phase 7 collects expert ratings and measures agreement, but does
not run A/B preference studies with multiple raters and consensus."*

**Where the fix belongs.** `courses/03-agentic-eval-harness/09_human_feedback_and_calibration.ipynb`,
the same notebook as G3.

**Why it matters.** Mostly because it is nearly free once G3 is closed — blinding and
randomising an existing two-rater comparison is a presentation change, not new machinery.

### G7 — Industry benchmarks are not discussed

**Guide item.** "What are evals?" → industry benchmarks, naming MMLU and the HuggingFace
leaderboard.

**Evidence.** One passing mention of MMLU in
`courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb`; zero occurrences
of `leaderboard`.

**Where the fix belongs.** A paragraph in
`courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §1, if anywhere.

**Why it matters — barely.** This repository is about application-specific evaluation, and the
guide itself frames benchmarks as the thing you move past. Listed for completeness; the honest
recommendation is one sentence saying why benchmarks are not the subject.

### G8 — The discrimination principle is applied but never stated

**Guide item.** *"LLMs are better at discriminating between options"* — therefore prefer
pairwise comparison, classification and scoring over open-ended generation.

**Evidence.** The principle is followed without being named.
`courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 5 uses `ArenaGEval`
pairwise; `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` uses `DAGMetric`
decision trees, which is forced classification. Neither says why that shape was chosen.

**Where the fix belongs.** `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb`
§4, which already carries the code-versus-judge decision but not the
open-ended-versus-discriminative one.

**Why it matters.** As written, a reader can reproduce the repo's judges but cannot derive the
shape of a new one. One paragraph converts three worked examples into a transferable rule.

---

## 5. Verdicts re-checked in the existing map

All eleven entries of `OPENAI_EDGE_CASE_COVERAGE`
(`courses/02-databricks-mlflow-evals/edge_cases.py`, line 274) were re-verified against the
repository as it stands. Every verdict was correct when written; one no longer is.

| Guide edge case | Recorded | Recorded justification | Today |
|---|---|---|---|
| Circular agent handoffs | `n/a` | "Single agent, no handoffs. Would require the multi-agent supervisor pattern" | **Stale.** `courses/03-agentic-eval-harness/02_tools_agents_and_supervisor_graph.ipynb` *is* that supervisor pattern, so the item is applicable and untested — see G1 |
| Multiple input modalities | `n/a` | "TelcoAssist is text-only" | **Holds.** All three courses are text-only |

The remaining nine hold as recorded: multilingual content, diverse formats, multiple intents,
typos and minimal context, ambiguous tool responses, jailbreak resistance, custom formatting
preferences, system/user prompt conflict, and long conversation histories — the last correctly
marked `partial`, since `courses/02-databricks-mlflow-evals/09_multiturn_and_tool_selection.ipynb`
covers 2–3 turns and the `p**n` arithmetic but nothing at 20+ turns.

---

## 6. Terminology divergences

Covered in substance, named differently. Each is a liability for interview preparation, where
the interviewer will use the guide's words rather than this repo's.

| The guide says | This repo says | Where |
|---|---|---|
| Data precision | Argument correctness | `courses/03-agentic-eval-harness/05_tool_call_evaluation.ipynb` §2.1, `ArgumentCorrectnessMetric` |
| Instruction following | Policy assertions | `courses/03-agentic-eval-harness/07_safety_and_policy_checks.ipynb` Part 1 |
| Functional correctness | Task completion; final-state check | `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb`; `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` Part 5 |
| Reference-guided grading | Reference-based metrics | `courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb` |

Two things run the other way — covered here, absent from the guide:

- **Same-model bias**, probed in `courses/03-agentic-eval-harness/08_building_custom_judges.ipynb`
  Part 6. The guide names position and verbosity bias but not this one.
- **Stratified reporting with a detection-limit argument**, in
  `courses/03-agentic-eval-harness/10_stratified_reporting_and_statistics.ipynb`.

---

## 7. Out of scope by design

Recorded so that the omissions read as decisions rather than misses.

| Guide item | Why it is not here |
|---|---|
| Reinforcement fine-tuning as the improvement lever | Declared out of scope in `courses/02-databricks-mlflow-evals/10_capstone_edge_cases_and_crossref.ipynb`. The repo's improvement lever is prompt optimisation — `courses/02-databricks-mlflow-evals/08_automated_improvement_gepa.ipynb` |
| Multimodal evaluation | All three courses are text-only. Audio and image inputs need a different agent, not a different evaluation technique |
| Purchased datasets | Listed by the guide as a data source; there is nothing to teach beyond the sentence |
| Long conversations at 20+ turns | Context-window pressure is a different regime. `p**n` degradation is covered; the regime is not |

---

## 8. Suggested order of work

| Order | Item | Why here | Size |
|---|---|---|---|
| 1 | **G1** circular handoffs | The system exists; only the test is missing | One notebook section |
| 2 | **G2** verbosity-bias probe | Part 5 of notebook 08 is a working template to clone | One notebook section |
| 3 | **§5** refresh the stale verdict | The cheapest correctness fix here — one dict entry and one table row | Minutes |
| 4 | **G3 + G6** multi-rater, then blinded comparison | Promotes an existing exercise into the built path; G6 then follows from it | One notebook section |
| 5 | **G5** n-gram metrics and the case against them | Fills a real hole in the course 01 taxonomy | One notebook section |
| 6 | **G8** state the discrimination principle | One paragraph, in the same notebook as G5 | Minutes |
| 7 | **G4** OpenAI Evals API and graders | A whole framework; belongs in `labs/`, not a course | A new lab |
| 8 | **G7** industry benchmarks | Low value for this repo's purpose | A paragraph, if at all |

---

## 9. A note on judge-model currency

The guide names `gpt-6-astra` as the recommended starting point for model graders. The judges
in this repository are older:

| Course | Judge model | Why |
|---|---|---|
| `courses/01-rag-agent-tool-evaluation/` | `gpt-4o`, `gpt-4o-mini` | Default at the time of writing |
| `courses/02-databricks-mlflow-evals/` | `gpt-4o`, `gpt-4o-mini`, plus Databricks-hosted endpoints | Default, with workspace models for phases 6–8 |
| `courses/03-agentic-eval-harness/` | `gpt-4.1-mini` | Deliberate — `gpt-4o-mini` fell into repetition loops. See `courses/03-agentic-eval-harness/README.md` line 149 |

This is not a coverage gap, and course 03's pin is load-bearing rather than neglected. But the
guide's own advice is to start with the most capable model and optimise downward, so a reader
holding both documents will notice the distance.
