# OpenAI Evaluation-Guide Coverage Gaps — Course 02 and Course 03

> An audit of this repository against OpenAI's
> [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices?api-mode=responses)
> guide, performed 2026-09-19. **Scoped per course**, because the two courses build different
> systems and therefore have different gaps — an item that is `n/a` for one is a live hole in
> the other. This document records only what is missing, partial or stale.

---

## 1. Scope and method

Every heading, metric, grader type, architecture pattern and anti-pattern in the guide was
extracted, then searched per course. Keyword hits were opened and read, not counted.


| Scope         | Files searched | What it is                                                                                                    |
| ------------- | -------------- | ------------------------------------------------------------------------------------------------------------- |
| **Course 02** | 23             | `courses/02-databricks-mlflow-evals/` — TelcoAssist, **one agent**, MLflow 3 GenAI on Databricks              |
| **Course 03** | 18             | `courses/03-agentic-eval-harness/` — a **multi-agent** supervisor + RAG, DeepEval and RAGAS                   |
| Repo-level    | 107            | All of `courses/`, `docs/`, `labs/`. Excludes `arize-phoenix-labs/` (third-party) and `archive/` (superseded) |


Verdicts: **Gap** (absent), **Partial** (prose only, or an exercise), **n/a** (the system makes  
it inapplicable), **Stale** (recorded in the repo's own map, no longer true).

---

## 2. Why one verdict is not enough

The two courses are deliberately different systems, so the guide lands on them differently.


|             | Course 02                             | Course 03                      |
| ----------- | ------------------------------------- | ------------------------------ |
| Agent shape | One agent, tools, no handoffs         | Supervisor + specialist agents |
| Frameworks  | MLflow 3 GenAI, Databricks            | DeepEval 4.x, RAGAS 0.4        |
| Ends at     | Online monitoring and judge alignment | A release gate wired to CI     |


**The consequence, stated once:** *circular agent handoffs* is correctly `n/a` for course 02 —
there are no handoffs — and is the single highest-value gap in course 03, which has the
supervisor graph that makes the failure reachable. A repo-wide verdict would have hidden both
halves of that.

---

## 3. Coverage matrix

The guide's checkable items, per course. ✅ covered · 🟡 partial · ❌ gap · — not applicable.


| Guide item                            | C02 | C03 | Note                                                                |
| ------------------------------------- | --- | --- | ------------------------------------------------------------------- |
| Eval-driven development               | ✅   | ✅   | C02 phase 0; C03 notebook 03                                        |
| Dataset from production traces        | ✅   | ✅   | C02 notebook 04; C03 notebook 12                                    |
| Stratified / unbiased dataset design  | ✅   | ✅   | C03 notebook 03 adds a datasheet                                    |
| Metric-based (deterministic) scorers  | ✅   | ✅   |                                                                     |
| LLM-as-judge                          | ✅   | ✅   |                                                                     |
| **Judge bias probes**                 | ❌   | 🟡  | **C02 has none.** C03 probes position and same-model, not verbosity |
| Human evaluation                      | 🟡  | 🟡  | Both stop at one rater                                              |
| Consensus / multi-rater               | ❌   | 🟡  | C03 leaves it as an exercise                                        |
| Blinded A/B preference                | ❌   | ❌   | Self-declared missing in C02                                        |
| Instruction following                 | ✅   | ✅   | C03 as policy assertions                                            |
| Functional correctness                | ✅   | ✅   | C03 adds a final-state DB check                                     |
| Tool selection                        | ✅   | ✅   |                                                                     |
| Data precision (argument correctness) | ✅   | ✅   |                                                                     |
| **Agent handoff accuracy**            | —   | ✅   | No handoffs in C02                                                  |
| **Circular handoffs**                 | —   | ❌   | **The key finding — see C3-1**                                      |
| Multi-turn / long conversations       | 🟡  | ❌   | C02 notebook 09 covers 2–3 turns; C03 does not cover multi-turn     |
| Edge cases (the guide's 11)           | ✅   | ✅   | C02 tracks them explicitly in code                                  |
| Jailbreak resistance                  | ✅   | ✅   |                                                                     |
| Continuous / online evaluation        | ✅   | ✅   |                                                                     |
| **Cost as a release gate**            | ❌   | ✅   | C03 gates at `$0.02` per resolved conversation                      |
| **Latency as a release gate**         | ❌   | ❌   | C02 measures it; C03 never mentions it                              |
| Improvement flywheel                  | ✅   | ✅   | C02 via GEPA; C03 via the loop in notebook 12                       |
| Reinforcement fine-tuning             | —   | —   | Out of scope by design                                              |
| Multimodal                            | —   | —   | Both are text-only                                                  |
| ROUGE / BLEU / BERTScore              | ❌   | ❌   | Absent repo-wide — see R-2                                          |
| OpenAI Evals API / Graders            | ❌   | ❌   | Absent repo-wide — see R-1                                          |


---

## 4. Course 02 gaps

`courses/02-databricks-mlflow-evals/`

### C2-1 — No judge-bias probe of any kind

**Guide item.** LLM-as-a-judge → challenges: position bias and verbosity bias.

**Evidence.** Zero occurrences of `position bias`, `verbosity bias` or any bias probe across
all 23 files. The word "bias" appears only as *dataset* bias — "the documented blind spot",
"hand-written sets are structurally blind" — which is a different anti-pattern.

**Why it matters.** This is also the map's own overstatement: notebook 10's cross-reference
claims *"LLM-as-judge, incl. bias caveats | Phases 2, 3, 7"*. Phase 7 aligns the judge against
human labels, which is valuable and is not a bias probe. See §7.

**Where the fix belongs.** `courses/02-databricks-mlflow-evals/07_judge_alignment_memalign.ipynb`.
`courses/03-agentic-eval-harness/08_building_custom_judges.ipynb` Part 5 is a working template.

### C2-2 — Human evaluation stops at one rater

**Guide item.** Human evals → consensus votes, multiple rounds, randomized blinded testing.

**Evidence.** Self-declared in notebook 10: *"Phase 7 collects expert ratings and measures
agreement, but does not run A/B preference studies with multiple raters and consensus."*

**Why it matters.** Phase 7's agreement statistics are the course's argument that the judge can
be trusted, and they are computed against a single rater's labels.

### C2-3 — Cost and latency are measured but gate nothing

**Guide item.** Not a guide item as such — a gap course 02 declares about itself, and worth
recording because course 03 half-closed it.

**Evidence.** Notebook 10: *"Both are measured (Phase 6) but neither gates a release."* Course
03 now gates cost at `max_cost_per_resolved_conversation: 0.02`; neither course gates latency.

### C2-4 — Long conversations beyond 2–3 turns

**Evidence.** Correctly recorded `partial` in `OPENAI_EDGE_CASE_COVERAGE`. Notebook 09 covers 2–3 turns and
the `p**n` arithmetic; context-window pressure at 20+ turns is untested.

**Not applicable to course 02:** circular handoffs, multi-agent handoff accuracy, multimodal —
all correctly recorded, all consequences of a single text-only agent.

---

## 5. Course 03 gaps

`courses/03-agentic-eval-harness/`

### C3-1 — Circular agent handoffs are never tested · **highest value in this document**

**Guide item.** Edge cases → contextual complexity → "circular agent handoffs".

**Evidence.** Zero occurrences of `circular`, `recursion_limit`, `max_iterations` or `max_steps`
in any of the 18 files. The supervisor and specialists that make the failure reachable are built
in `02_tools_agents_and_supervisor_graph.ipynb`; nothing bounds the loop between them.

**Where the fix belongs.** `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb`.

**Why it matters.** This is the only gap in the document where the system already exists and
only the test is missing. It is also the item course 02 ruled `n/a` on the grounds that there
are no handoffs — true there, and the reason this gap went unnoticed. See §7.

### C3-2 — Verbosity bias is stated but never probed

**Guide item.** LLM-as-a-judge → "verbosity bias"; "control for response length".

**Evidence.** Notebook 08 probes two biases — position (Part 5) and same-model (Part 6) — and
not verbosity. The insight exists in prose only, at `docs/interview-prep/QUESTION_BANK.md`
line 2962: *"Longer answers win pairwise comparisons at a rate unrelated to quality."* No judge
in the course controls for response length.

**Where the fix belongs.** Notebook 08, beside Part 5 — the position-bias probe is the shape.

**Why it matters.** Notebook 12's canary compares a new build against the shipped one. If the
new build is chattier, part of the win is word count.

### C3-3 — Multi-rater consensus is a reader exercise

**Guide item.** Human evals → consensus votes for aggregation.

**Evidence.** `09_human_feedback_and_calibration.ipynb` names the need — *"`labeller` — because
inter-annotator agreement needs at least two of them"* — then defers it to *"Exercise 2"*. The
built path runs one labeller, while Cohen's and weighted kappa are taught as core.

### C3-4 — Latency is not gated, and not mentioned

**Evidence.** `11_the_release_gate_and_ci.ipynb` gates four things — safety, aggregate drop,
per-stratum floors, cost. The words `latency` and `p95` do not appear in the notebook at all.

**Why it matters.** Cost made it into the gate and latency did not, which reads as an omission
rather than a decision. A correct answer that takes nine seconds is a different failure.

### C3-5 — Multi-turn conversation is not evaluated

**Guide item.** Edge cases → "long conversation histories".

**Evidence.** Only 2 of 18 files mention multi-turn at all. Course 02 owns this topic
(notebook 09); course 03 evaluates single exchanges throughout.

---

## 6. Repo-level gaps

Neither course's fault — these belong to the taxonomy or to `labs/`.


| ID      | Gap                                      | Evidence                                                                                                                                                                | Where it belongs                                                        |
| ------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **R-1** | OpenAI Evals API and Graders tool        | Zero occurrences of `Evals API`, `client.evals`, `grader` anywhere                                                                                                      | A new lab under `labs/`, beside `labs/llm-as-judge/`                    |
| **R-2** | ROUGE / BLEU / BERTScore / perplexity    | Zero occurrences across all 186 tracked files, as technique **and** as critique. The guide gates its worked example on ROUGE-L ≥ 0.40 and names BLEU as an anti-pattern | `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §1 |
| **R-3** | Industry benchmarks (MMLU, leaderboards) | One passing MMLU mention; zero `leaderboard`                                                                                                                            | Course 01 §1, one paragraph, if at all                                  |
| **R-4** | The discrimination principle, unstated   | Applied in C03 notebooks 07 and 08, never named as a rule a reader could reuse                                                                                          | Course 01 §4, beside the code-vs-judge decision                         |


---

## 7. Three claims in course 02's map that no longer hold

`courses/02-databricks-mlflow-evals/edge_cases.py` — the `OPENAI_EDGE_CASE_COVERAGE`
dict — and notebook 10 carry the repo's
only other cross-reference to this guide. Both say *"this track"* and mean course 02 alone.
Three of their claims have since drifted.


| Claim                                                                                                          | Recorded    | Today                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| *"Circular agent handoffs — n/a. Single agent, no handoffs. Would require the multi-agent supervisor pattern"* | `n/a`       | **Stale at repo level.** Course 03 *is* that pattern — the item is applicable and untested. See C3-1                                          |
| *"LLM-as-judge, incl. bias caveats — Phases 2, 3, 7"*                                                          | Covered     | **Overstated.** Course 02 has no bias probe; phase 7 measures human agreement, which is a different check. See C2-1                           |
| *"Multi-agent handoff accuracy — Not covered"*                                                                 | Not covered | **Resolved elsewhere.** `courses/03-agentic-eval-harness/06_agent_handoff_and_end_to_end.ipynb` covers routing accuracy and handoff integrity |


The remaining nine edge-case verdicts were re-verified and hold, including *multiple input
modalities — n/a* (both courses are text-only) and *long conversation histories — partial*.

---

## 8. Terminology divergences

Covered in substance, named differently. A liability for interview preparation, where the
interviewer uses the guide's words.


| The guide says           | This repo says                     | Where                                                                                                                          |
| ------------------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Data precision           | Argument correctness               | C03 `05_tool_call_evaluation.ipynb` §2.1, `ArgumentCorrectnessMetric`                                                          |
| Instruction following    | Policy assertions                  | C03 `07_safety_and_policy_checks.ipynb` Part 1                                                                                 |
| Functional correctness   | Task completion; final-state check | `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb`; C03 `06_agent_handoff_and_end_to_end.ipynb` Part 5 |
| Reference-guided grading | Reference-based metrics            | `courses/01-rag-agent-tool-evaluation/04_Generator_Metrics_Reference_Based.ipynb`                                              |


Two run the other way — covered here, absent from the guide: **same-model bias**
(C03 notebook 08 Part 6) and **stratified reporting with a detection limit**
(C03 `10_stratified_reporting_and_statistics.ipynb`).

---

## 9. Out of scope by design


| Item                      | Why                                                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Reinforcement fine-tuning | Declared out of scope in C02 notebook 10. The improvement lever here is prompt optimisation — `08_automated_improvement_gepa.ipynb` |
| Multimodal evaluation     | Both courses are text-only. Audio and image need a different agent, not a different technique                                       |
| Purchased datasets        | A data source the guide lists; nothing to teach beyond the sentence                                                                 |


---

## 10. Suggested order of work


| Order | Item                                                     | Scope     | Why here                                                       |
| ----- | -------------------------------------------------------- | --------- | -------------------------------------------------------------- |
| 1     | **C3-1** circular handoffs                               | Course 03 | The system exists; only the test is missing                    |
| 2     | **C3-2** verbosity-bias probe                            | Course 03 | Notebook 08 Part 5 is a template to clone                      |
| 3     | **§7** correct the three drifted claims                  | Course 02 | Cheapest correctness fix here — one dict entry, two table rows |
| 4     | **C2-1** a bias probe for course 02                      | Course 02 | Closes a gap the map currently claims is covered               |
| 5     | **C3-3 + C2-2** multi-rater, then blinded A/B            | Both      | Promotes an existing exercise into the built path              |
| 6     | **C3-4** latency in the gate                             | Course 03 | Cost is already there; latency is the missing twin             |
| 7     | **R-2 + R-4** n-gram metrics and the discrimination rule | Course 01 | Two sections in the taxonomy notebook                          |
| 8     | **R-1** OpenAI Evals API                                 | `labs/`   | A whole framework; a new lab, not a course section             |
| 9     | **R-3** industry benchmarks                              | Course 01 | Low value for this repo's purpose                              |


---

## 11. A note on judge-model currency

The guide names `gpt-6-astra` as the starting point for model graders. These are older:


| Course    | Judge model                                   | Why                                                                                                         |
| --------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Course 01 | `gpt-4o`, `gpt-4o-mini`                       | Default at the time of writing                                                                              |
| Course 02 | `gpt-4o`, `gpt-4o-mini`, Databricks endpoints | Default, plus workspace models for phases 6–8                                                               |
| Course 03 | `gpt-4.1-mini`                                | Deliberate — `gpt-4o-mini` fell into repetition loops. `courses/03-agentic-eval-harness/README.md` line 149 |


Not a coverage gap, and course 03's pin is load-bearing. But the guide's advice is to start
with the most capable model and optimise downward.