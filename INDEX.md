# Document index

A lookup table, not a starting point. `README.md` answers *"where do I begin?"*; this file
answers **"I need to know about X — which file, and which section of it?"**

Everything here is prose or notebooks. Nothing on this page executes.

**Everything under `docs/` is also served at https://eval-demystified.vercel.app** — Vercel
project `eval-demystified`, built from `main` by `site/build.py`, so a push to `main` updates
the site. The rendered pages keep these section numbers; the URL slugs are the second field of
each `RENDER` / `COPY` entry in `site/build.py` (the field guide is `field-guide.html`, the
question bank `question-bank.html`, the roadmap `roadmap.html`, the drill
`evaluation-round-drill.html`).

---

## 1. Find it by topic

**The five short names used in every table below:**

| Short name | Is this file | What it is |
|---|---|---|
| **Field guide** | [`docs/concepts/rag-agent-tool-evaluation.md`](docs/concepts/rag-agent-tool-evaluation.md) | Course 01 theory. Tool-agnostic: what each check catches and misses, no framework APIs |
| **Question bank** | [`docs/interview-prep/QUESTION_BANK.md`](docs/interview-prep/QUESTION_BANK.md) | 35 questions + 30 metric questions + 19 cases + appendices |
| **Databricks ref** | [`docs/concepts/databricks-mlflow-evals.md`](docs/concepts/databricks-mlflow-evals.md) | Course 02 theory. Framework-specific: MLflow scorers, gotchas, the numbers |
| **Drill page** | [`docs/interview-prep/evaluation-round-drill.html`](docs/interview-prep/evaluation-round-drill.html) | The self-quiz. Open in a browser |
| **Case study** | [`docs/concepts/customer-support-multi-agent-case-study.md`](docs/concepts/customer-support-multi-agent-case-study.md) | One multi-tenant support system evaluated stage by stage, through the gate, canary and online signals |
| **Cost doc** | [`docs/concepts/cost-tracking-and-guardrails.md`](docs/concepts/cost-tracking-and-guardrails.md) | The same system's cost tracking, budgets and guardrails |
| **Online/offline** | [`docs/concepts/databricks-mlflow-evals.md`, Part 5](docs/concepts/databricks-mlflow-evals.md#part-5--online-vs-offline) | The two regimes and what flows between them; the sampling-resolution argument is in explainer 05 §6 |

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
| Offline vs online, and what can never go online | Field guide **§4.1**; question bank **Q18**; online/offline **§1**, **§6** |
| Sampling rates and alerting | Field guide **§4.2**; Databricks ref **Part 4**; online/offline **§5** (**§5.1** in plain English) |
| Release gating — thresholds *and* no-regression | Question bank **Part 6**, **Case 13**; course 03 notebook **11** (four checks, four scenarios) |
| A gate as a decision layer rather than another metric | Course 03 notebook **11**; `courses/03-agentic-eval-harness/ci/apply_gate.py` |
| Stratified reporting — gating on the worst segment, not the mean | Course 03 notebooks **04** and **10** |
| Evaluating the human approval step itself (rubber-stamping) | Course 03 notebook **09** |
| Final-state checks against a database ("exactly once") | Course 03 notebook **06** |
| Silent failures that look like success | Databricks ref **Part 3**; question bank **Appendix A** |
| Judge alignment, agreement measures, quadratic weighted kappa | Databricks ref **Part 4**; question bank **Q15**, **Case 10** |
| Wilson intervals, sample size, "is this drop real?" | Databricks ref **Part 4**; question bank **Q21**; online/offline **§5.1** |
| Cost control | Question bank **Part 9**, **Case 19** |
| Fill-in templates: scorecard, failure investigation, acceptance criteria, regression report | `docs/study-guide/evaluation-templates.md` **§1–§4** |

### Interview preparation

| Looking for | Go to |
|---|---|
| A reading path with time estimates | `docs/study-guide/evaluation-study-plan.html` |
| The complete basic → expert path — ten levels with exit checks, plus OpenAI-round and Databricks sections | `docs/study-guide/evaluation-roadmap.md` |
| Self-quiz with hidden answers and per-item scoring | `evaluation-round-drill.html` |
| 35 situational questions | Question bank **Parts 1–9** |
| 30 metric-level questions | Question bank **Part 10** |
| 19 long-form cases | Question bank **Tiers A–H** |
| The Decomposition Spine (8 steps) | Question bank **§0.2** |

---

## 2. The documents

### `docs/concepts/rag-agent-tool-evaluation.md` — Field guide (15,900 words)

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

### `docs/concepts/databricks-mlflow-evals.md` — Databricks/MLflow reference (11,100 words)

The theory companion to course 02. Framework-specific, where the field guide is not.

| | Covers |
|---|---|
| **Part 1** | TelcoAssist, the agent under test: tools, data, models, trace shape, deliberate non-goals |
| **Part 2** | Concept map by theme, each pointing at the phase that demonstrates it. Appendix A: what this track measures (built-in scorers, guidelines, quality gates). Appendix B: the wider metric landscape and the naming map across three vocabularies |
| **Part 3** | 32 gotchas as symptom → cause → fix, led by the silent failures |
| **Part 4** | The numbers, thresholds, decision rules, scorer prerequisites, agreement measures, phase map |

### `docs/concepts/customer-support-multi-agent-case-study.md` — Support-system case study (10,300 words)

One multi-tenant customer-support system (supervisor, order, refund and RAG agents) evaluated
end to end. Where the field guide defines each check, this applies all of them to one system.

| | Covers |
|---|---|
| **§1–§4** | The scenario and its scale targets · RAG agent vs multi-agent, two shapes one harness · architecture · one real request traced |
| **§5–§16** | Every stage's deterministic and judged checks: input, tenant resolution, router (confidence floor 0.7→0.82), delegation, RAG retrieval and answer (the 11-row scorer map, thresholds), tool selection and arguments, action and policy, trajectory, final response, instruction following |
| **§17–§24** | Dataset design · instrumentation · the offline suite and metrics · human evaluation and judge calibration · versioned rubrics · candidate vs production · pairwise evaluation |
| **§25–§30** | The release gate's four checks and scenarios · canary · online deterministic and judged evaluation · product signals · the feedback loop |
| **§31–§38** | Eval-driven architecture · the complete architecture, offline flow and lifecycle · deterministic vs judged, final view · coverage · the mental model · what to remember, with eight interview mistakes |

### `docs/concepts/cost-tracking-and-guardrails.md` — Cost and guardrails (3,400 words)

The case study's system again, from the cost side. Diagram source:
`cost-tracking-and-guardrails.excalidraw` (rendered as `cost-tracking-and-guardrails.png`).

| | Covers |
|---|---|
| **§1–§4** | Scenario · architecture · one request · its cost trace |
| **§5–§9** | Cost tracking per LLM call, RAG step, tool and agent · tenant-level attribution |
| **§10–§15** | Cost guardrails: per-request budgets, dynamic budgets, model routing, RAG cost limits, tenant budgets |
| **§16–§24** | Five guardrail boundaries: input, agent, RAG/data, tool/action ("agent recommends, policy decides, executor acts"), output · deterministic vs AI guardrails · what happens when one triggers |
| **§25–§29** | Cost, guardrails and evaluation together · production monitoring · cost as a blocking release check · the mental model |

### `docs/interview-prep/QUESTION_BANK.md` — Question bank (48,100 words)

Everything for the evaluation thread of a system-design round, in one file.

| | Covers |
|---|---|
| **Part 0** | What the round measures (five scoring axes) · the Decomposition Spine · the evaluation taxonomy |
| **Parts 1–9** | 35 questions. Each: the issue underneath, what they're checking, a strong answer, a weak answer *with why it reads badly*, and the follow-up to expect |
| **Part 10** | 30 metric-level questions, grouped by evaluation surface — the ones asked with your dashboard on screen |
| **Tiers A–H** | 19 cases, 30–45 minutes each: strategy from zero · diagnosing production · trajectory and multi-agent · judges and calibration · gating and CI · monitoring · adversarial · platform |
| **Appendices A–G** | Silent-failure catalogue · misreadings that sound like insight · company-specific flavour · rapid-fire drill · closing notes · interview scorecard · production scenarios |

### `docs/guide-audits/openai-eval-guide-coverage-gaps.md` — OpenAI guide repo coverage (3,800 words)

Maps every topic in OpenAI's *Evaluation best practices* guide to where this repo teaches it,
and names what is missing. Verdicts are taken **per course**, because a repo-wide average
hides whichever course is weaker.

| | Covers |
|---|---|
| **Header** | Tally by badge — 47 ✅ · 2 🟡 · 5 ⏭️ · 1 ❌ across 55 rows — and the headline finding |
| **§1–§7** | The guide's own sections as mapping tables: what are evals · design the process · where evals go by architecture · types of evaluator · the 11 edge cases · improvement · platform surface |
| **The gap list** | Five tracked gaps, four **closed** 2026-09-20 — circular handoffs, verbosity bias, blinded preference testing, ROUGE/BLEU/BERTScore. Only the OpenAI Evals API remains open |
| **When a gap is worth closing** | The rule separating the four descopes from the four gaps, and why scoping per course is what made two of them visible |
| **Corrections** | Three claims in course 02's own cross-reference that had drifted — one stale, one overstated, one resolved elsewhere — all corrected 2026-09-20 |
| **Terminology · Related · What moves the needle** | Four renamings the guide uses · the two companion documents · the cheapest two actions |

### `docs/guide-audits/openai-eval-guide-tutorial.md` — Evaluation tutorial + tracker (4,300 words)

The lesson to the audit's record. OpenAI's guide walked through in plain language — 3–4 lines
per concept, the notebook that teaches it, and a TODO that asks you to produce something
rather than read something. The file is its own progress tracker.

| | Covers |
|---|---|
| **Header** | How to use the tracker, `grep` progress commands, and which TODOs cost money |
| **§1** | What an eval is · the n-gram family and the one example that settles it (ROUGE-L 0.94 for a false answer, 0.09 for a true one) |
| **§2** | The five steps — define good, collect real cases, checkable metrics, paired comparison, keep measuring |
| **§3** | Where checks go by system shape · tool choice vs arguments · final-state verification · routing, handoffs and loops · reporting by segment |
| **§4** | Code vs judge vs human · building a judge three ways · the three judge biases · the length-controlled probe · kappa · blinded preference testing |
| **§5–§6** | Edge cases by kind, the polite tool failure · the improvement loop and why judge alignment comes before prompt optimisation |
| **§7** | An eight-step path through the repo, and the four-step version for one evening |

Published on the site as `openai-eval-guide-tutorial.html`, rendered from this Markdown (the
earlier hand-built HTML version is in `archive/`).

### `docs/study-guide/evaluation-roadmap.md` — Evaluation roadmap (4,400 words)

The complete path through the repository ordered by **skill level**, where the study plan is
ordered by what the round tests and the tutorial's §7 is the shortest route. Ten levels in four
bands; every item carries what it teaches, what running it costs, and a *you are done when you
can…* check.

| | Covers |
|---|---|
| **The ladder** | Levels 0–9: orientation · RAG · agents · ground truth · judges · statistics · the gate · online · safety and multi-agent · the harness as a product. ~54 hours end to end |
| **OpenAI** | The five scoring axes, the Spine, the two follow-ups to expect with where the repo answers them, Agents SDK vocabulary mapped to the checks practised here, the guide audit tally, what must be learned outside the repo (the Evals API), a three-day plan |
| **Databricks** | Course 02's ten phases as the ladder, the concepts to state grouped basic → expert (span contracts, prerequisites, six aggregations, two-condition promotion, online eligibility, sampling, weighted kappa, GEPA through the same gate), the three-vocabulary naming map, environment realities |
| **Fast paths** | One hour, one evening, one weekend, two weeks, interview-only — and where the money goes |

### `docs/study-guide/evaluation-templates.md` — Evaluation templates (1,700 words)

Four fill-in documents, each with when to use it, the template as tables or a checklist, and
links to the explainers that teach its fields. Copy one and fill in the empty column.

| | Covers |
|---|---|
| **§1 Scorecard** | One evaluated build on one page: run identity and versions, per-metric target / result / interval / worst stratum, safety as case IDs, verdict, risks, next actions, known gaps |
| **§2 Failure investigation** | One failure: input, provenance of the expectation, versions, an eight-step layer checklist (retrieval → measurement), first broken layer, root cause, the regression case added |
| **§3 Acceptance criteria** | The bar agreed before results exist: scope, criteria with thresholds and blocking flags, must-never list, escalation, launch and rollback rules, residual risks, sign-off by role |
| **§4 Regression report** | Candidate vs live baseline on the same cases: what changed, paired deltas with intervals, flipped cases, new safety violations, strata under their floor, the ship decision and who made it |

### `docs/study-guide/evaluation-topic-notebook-mapping.md` — Topic & notebook mapping (2,600 words)

The lookup companion to the roadmap above. The roadmap carries the narrative — goal and
self-check per level; this file carries every topic &rarr; notebook/resource &rarr; cost table,
one per level, so neither document has to hold both jobs.

| | Covers |
|---|---|
| **Cost key** | none (no API calls) · key (live `OPENAI_API_KEY` calls) · cached (judged once, replayed from `data/score_cache/`) · workspace (a real Databricks workspace) |
| **Levels 0–9** | One table per level, each row a notebook or doc, what it teaches, and its cost — the same ten levels as the roadmap, in lookup form |

### `docs/about.md` — About the site (220 words)

Who maintains the site, how to report a problem (GitHub issues), how the site is built, the
privacy line, and the licences.

### `docs/CHANGELOG.md` — Changelog

What changed on the site, by date, newest first. Add an entry with every change a reader
would notice.

### The four interactive HTML pages

Open in a browser. No build step, no server, no API key.

| File | What it does |
|---|---|
| `docs/study-guide/evaluation-study-plan.html` | Seven stages ordered by what the round tests, with time estimates, a 2–3 day fast path, a skip list and a readiness check. Tick items off as you go |
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

### The roadmap-level explainers

`docs/roadmap-explainers/NN-*.md` — one plain-language walkthrough per level of the
[evaluation roadmap](docs/study-guide/evaluation-roadmap.md), pulled together from that
level's notebooks, field guide sections, labs and question-bank entries, with nothing
repeated twice. Sequential, with prev/next links between them; each is self-contained
and does not require reading the roadmap first. Ten levels, plus a Level 10 cram sheet
that synthesises all ten into one end-to-end mental model and introduces nothing new.

| Level | File | The question it answers |
|---|---|---|
| 0 &middot; Beginner | `00-orientation` | Draw the five-layer taxonomy from memory and choose between a deterministic scorer and a judge without hesitating |
| 1 &middot; Beginner | `01-rag-retrieval-and-generation` | Separate a retrieval failure from a generation failure with numbers, and know the one failure no referenceless metric can see |
| 2 &middot; Intermediate | `02-agents-tools-conversations-trajectories-outcomes` | Hold three things apart &mdash; mechanics, process, outcome &mdash; and reach for the system of record before any judge |
| 3 &middot; Intermediate | `03-ground-truth` | Know where cases and labels come from on day one and by month three, and the two ways a dataset lies to you |
| 4 &middot; Intermediate | `04-judges-and-the-humans-who-validate-them` | Build a judge three ways, catch it lying three ways, and know the only thing that licenses trusting it |
| 5 &middot; Advanced | `05-statistics-and-stratified-reporting` | Refuse to act on a number you cannot resolve, and never report an average that buries a segment |
| 6 &middot; Advanced | `06-the-release-gate-and-ci` | Turn metrics into a decision that can refuse a deploy, and put the cost of loosening it on a named line |
| 7 &middot; Advanced | `07-online-evaluation-and-the-loop` | Measure without an answer key, alert only on what you can resolve, and carry every finding back into a gated test |
| 8 &middot; Expert | `08-safety-adversarial-and-multi-agent-attribution` | Separate what must never happen from what should usually happen, test by attack surface, and say which agent broke a multi-agent run |
| 9 &middot; Expert | `09-the-harness-as-a-product` | Keep the evaluation system itself trustworthy and affordable &mdash; the layer above the metrics |
| 10 &middot; Cram | `10-the-enterprise-harness-end-to-end` | Build the whole enterprise harness as one six-stage loop &mdash; contract, ground truth, offline, gate and CI, production and online, human feedback &mdash; and name the trap at every stage |

### `archive/roadmap-explainers-org/00-orientation.md` — original edition of Level 0, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. The five things you can actually evaluate · 2. The one question that splits every metric in two: does it need an answer key? · 3. LLM-as-judge: powerful, but not an oracle · 4. The decision you'll make constantly: code, or a judge? · 5. The cost ladder for building a check (which rung do you actually need?) · 6. The other cost ladder: what it costs in real dollars to *run* a notebook or check · 7. The tooling landscape: four frameworks, two shapes · 8. Offline vs. online: the two questions that decide where a check can run · Question-bank corner — what a decomposition round pushes on · References |

### `docs/roadmap-explainers/00-orientation.md` — Level 0, Orientation: What There Is to Evaluate (4,000 words)

| | Covers |
|---|---|
| **Sections** | 1. Separate the Five Things You Can Evaluate · 2. Ask Whether the Check Needs an Answer Key · 3. Treat the Judge as an Instrument, Not an Oracle · 4. Reach for Code Before Reaching for a Judge · 5. Climb the Scorer Ladder Only When Forced · 6. Decide Where a Check Can Run Before Building It · 7. Rehearse the Decomposition Round · Key Takeaways · Check Yourself · References |
| **Note** | Decompose the system before measuring it, because one quality score cannot say which stage broke. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/01-rag-retrieval-and-generation.md` — original edition of Level 1, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. The RAG pipeline, and why you evaluate its two halves separately · 2. Deterministic retrieval metrics: four numbers that are supposed to disagree · 3. LLM-judged retrieval metrics: three metrics because there are three failures · 4. Generation without a reference: three ways "the answer is wrong" can happen · 5. Generation against a reference: Answer Correctness and Semantic Similarity · 6. Writing a rubric that doesn't produce a vague judge · 7. Evaluation as pipeline gates, not just after-the-fact scoring · 8. RAGAS as a second opinion, and the pytest/CI batch pattern · 9. Building a RAG system and synthesizing a golden set · 10. Reading the results · Question-bank corner — retrieval and generation numbers, live on a dashboard · References |

### `docs/roadmap-explainers/01-rag-retrieval-and-generation.md` — Level 1, RAG: Retrieval and Generation (5,900 words)

| | Covers |
|---|---|
| **Sections** | 1. Evaluate the Two Halves Separately · 2. Count What the Retriever Found, Before Any Judge · 3. Ask a Judge Three Questions, Not One · 4. Score the Answer With No Reference, and Know What That Cannot See · 5. Check Correctness Against a Reference · 6. Write the Rubric, or the Judge Writes It for You · 7. Gate the Pipeline, Don't Only Score It Afterwards · 8. Build the System and Synthesize Its Golden Set · 9. Read the Table by Pattern, Not by Headline · 10. Rehearse the Decomposition Questions · Key Takeaways · Check Yourself · References |
| **Note** | The same Level 1 content as the page above, restyled: trade-off tagline, reading time, imperative headings, argument-carrying prose in place of bullet runs, plus takeaways and a 10-question self-check. No framework tours: field and metric vocabulary is kept and glossed, but library class inventories and API mechanics are out, and the practice questions are reproduced in full rather than pointing at the question bank. Kept alongside the original for comparison. |

### `archive/roadmap-explainers-org/02-agents-tools-conversations-trajectories-outcomes.md` — original edition of Level 2, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Multi-turn conversational evaluation · 2. Tool-use metrics: the mechanics layer · 3. Task completion and outcome verification · 4. Agent trajectory evaluation: the nine trace-level checks · Question-bank corner — the design-round follow-ups this level answers · References |

### `docs/roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.md` — Level 2, Agents: Tools, Conversations, Trajectories, Outcomes (4,600 words)

| | Covers |
|---|---|
| **Sections** | 1. Score the Conversation, Not Just the Turn · 2. Check the Mechanics: Right Tool, Right Arguments · 3. Verify the Outcome, Not the Sentence · 4. Judge the Path, Not Only Where It Ended · 5. Rehearse the Design-Round Follow-Ups · Key Takeaways · Check Yourself · References |
| **Note** | Score mechanics, process and outcome separately, because passing any one of the three says nothing about the other two. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/03-ground-truth.md` — original edition of Level 3, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Case anatomy — six expectations, not one · 2. Stratification and the refusal quota · 3. Dataset datasheets · 4. Mining production traces into eval datasets · 5. Provenance and merge-by-input-hash · 6. Synthesized vs. hand-authored cases · 7. The two ways a dataset lies to you · Question-bank corner — ground truth and datasets · References |

### `docs/roadmap-explainers/03-ground-truth.md` — Level 3, Ground Truth: Where Cases and Labels Come From (4,800 words)

| | Covers |
|---|---|
| **Sections** | 1. Pin Six Expectations, Not One · 2. Stratify Before Writing, and Keep a Refusal Quota · 3. Ship a Datasheet With the Dataset · 4. Mine Traffic for Inputs, Never for Labels · 5. Record Who Decided, and Merge by Input · 6. Run a Curated Set and a Mined Set With Opposite Policies · 7. Name the Two Ways a Dataset Lies · 8. Rehearse the Ground-Truth Questions · Key Takeaways · Check Yourself · References |
| **Note** | Collect inputs from real traffic but never labels from the system under test, because a dataset built from its own answers can only agree with itself. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/04-judges-and-the-humans-who-validate-them.md` — original edition of Level 4, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Building a judge, three ways · 2. Custom scorers: spend judgement where judgement is actually needed · 3. Judge bias: the three specific ways a judge lies · 4. Human feedback: three kinds, and only one can calibrate a judge · 5. Calibration: agreement, and agreement above chance · 6. Judge alignment: turning expert disagreement into a better judge · 7. Blinded preference testing, and why it needs a second rater · 8. The rubber-stamp signal: evaluating the human, not just the record · Question-bank corner · References |

### `docs/roadmap-explainers/04-judges-and-the-humans-who-validate-them.md` — Level 4, Judges, and the Humans Who Validate Them (6,100 words)

| | Covers |
|---|---|
| **Sections** | 1. Build the Judge in One of Three Shapes · 2. Spend Judgement Only Where Judgement Is Needed · 3. Test the Three Ways a Judge Lies · 4. Collect the One Kind of Human Feedback That Calibrates · 5. Measure Agreement Above Chance, Not Raw Agreement · 6. Align the Judge on Expert Disagreement · 7. Blind the Preference Test, and Use Two Raters · 8. Check the Approver, Not Just the Approval · 9. Rehearse the Judge Questions · Key Takeaways · Check Yourself · References |
| **Note** | A judge is the only way to score open-ended text at scale, and it cannot be trusted until it is measured against the people who do not scale. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/05-statistics-and-stratified-reporting.md` — original edition of Level 5, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Stratified reporting: score each slice, not the whole · 2. Sample size: could your suite even see the change? · 3. The small-stratum rule: when a group is too small to gate on · 4. Paired comparison and McNemar's test · 5. Confidence intervals: bootstrap and Wilson · 6. The same problem in production: the sampling-resolution problem · 7. Simpson's paradox: when every stratum improves and the total falls · 8. Putting it together · Question-bank corner — the two rounds this level prepares you for · References |

### `docs/roadmap-explainers/05-statistics-and-stratified-reporting.md` — Level 5, Statistics and Stratified Reporting (4,000 words)

| | Covers |
|---|---|
| **Sections** | 1. Score Each Slice, Not the Whole · 2. Ask Whether the Suite Could See the Change · 3. Report a Small Stratum Without Gating on It · 4. Compare the Same Cases, Not Two Samples · 5. Put an Interval Around Every Number · 6. Buy the Sample Rate That Can See the Regression · 7. Watch for Every Stratum Improving While the Total Falls · 8. Combine the Four Tools · 9. Rehearse the Reporting Questions · Key Takeaways · Check Yourself · References |
| **Note** | Gate on the worst slice rather than the average, because a group is only as loud in the mean as it is big. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/06-the-release-gate-and-ci.md` — original edition of Level 6, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. A gate is not another metric · 2. The four checks, in order · 3. Why a threshold alone is not enough — the erosion problem · 4. Tolerance has to be set per metric type · 5. Free CI gate vs. paid evaluation job · 6. Prompt registry and production aliasing · 7. The two-condition promotion gate, worked through a real prompt edit · 8. Optimizer scores vs. the same gate · 9. What a gate is not · Question-bank corner — what this level's interview material adds · References |

### `docs/roadmap-explainers/06-the-release-gate-and-ci.md` — Level 6, The Release Gate and CI (5,600 words)

| | Covers |
|---|---|
| **Sections** | 1. Separate the Gate From the Metric · 2. Run Four Checks, and Block on Any One · 3. Check Both the Threshold and the Regression · 4. Set Tolerance by Metric Type · 5. Decide Free on Every Push, Score on Demand · 6. Register a Prompt Without Deploying It · 7. Promote Only What Clears Both Conditions · 8. Put Machine-Written Prompts Through the Same Gate · 9. Know What a Gate Is Not · 10. Rehearse the Gate Questions · Key Takeaways · Check Yourself · References |
| **Note** | Gate against what is live, not against a fixed bar, because a system can lose seven points without any single release ever failing. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/07-online-evaluation-and-the-loop.md` — original edition of Level 7, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. The fact that decides everything: production has no ground truth · 2. Reference-free production metrics: three techniques, no answer key · 3. Sampling: cheap checks on everything, judges see a slice · 4. The five standard alerts · 5. Incident drills: proving which alert catches what · 6. The canary: the only online question that's properly answerable · 7. Closing the loop · 8. Live tracing in Phoenix, and two genuinely new ideas · Question-bank corner — offline → online · References |

### `docs/roadmap-explainers/07-online-evaluation-and-the-loop.md` — Level 7, Online Evaluation and the Loop (5,000 words)

| | Covers |
|---|---|
| **Sections** | 1. Accept That Production Has No Ground Truth · 2. Score Consistency and Shape Instead of Correctness · 3. Sample the Judges, Never the Free Checks · 4. Alert on Shape, Not on Quality · 5. Drill the Alerts to Learn What They Miss · 6. Ask Whether the New Build Beats the Old One · 7. Turn Every Finding Into a Permanent Test · 8. Trace Live, and Judge the Tool's Own Output · 9. Rehearse the Online Questions · Key Takeaways · Check Yourself · References |
| **Note** | Every check that needs an answer key dies at deployment, and it dies silently — reporting "skipped" rather than failing. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/08-safety-adversarial-and-multi-agent-attribution.md` — original edition of Level 8, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Safety assertions that never get averaged · 2. Routing confusion matrices and handoff integrity · 3. Circular-handoff detection and blame attribution · 4. Adversarial design by attack surface · 5. Consent and approval gating between turns · Question-bank corner · Key checks to carry forward · References |

### `docs/roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md` — Level 8, Safety, Adversarial Testing, and Multi-Agent Attribution (5,600 words)

| | Covers |
|---|---|
| **Sections** | 1. Report Safety as a List, Never a Rate · 2. Read the Routing Matrix, Not the Accuracy · 3. Detect Loops and Attribute Blame · 4. Design Adversarial Tests by Attack Surface · 5. Gate Consent Between Turns · 6. Rehearse the Safety Questions · Key Takeaways · Check Yourself · References |
| **Note** | Report safety as a list of case IDs rather than a percentage, because a percentage cannot be opened and read. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/09-the-harness-as-a-product.md` — original edition of Level 9, superseded

| | Covers |
|---|---|
| **Sections** | Why this level exists · 1. Keeping the measuring instrument honest · 2. Repo conventions that keep every number traceable · 3. Eval-driven development — deciding "good" before the code exists · 4. What the harness still doesn't do — the open gaps · Question-bank corner — cost, ownership, decay, and building a platform · References |

### `docs/roadmap-explainers/09-the-harness-as-a-product.md` — Level 9, The Harness as a Product (6,200 words)

| | Covers |
|---|---|
| **Sections** | 1. Keep the Measuring Instrument Honest · 2. Choose Conventions That Keep Every Number Traceable · 3. Decide "Good" Before the Code Exists · 4. Name What the Harness Still Doesn't Do · 5. Rehearse the Cost, Ownership and Decay Questions · Key Takeaways · Check Yourself · References |
| **Note** | A harness that only computes numbers is not yet a product, because nobody has agreed what the numbers must reach or who signs off on them. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### `archive/roadmap-explainers-org/10-the-enterprise-harness-end-to-end.md` — original edition of Level 10, superseded

| | Covers |
|---|---|
| **Sections** | Why this page exists · 1. Stage ① — The contract: decide "good" before the code exists · 2. Stage ② — Ground truth: the golden set · 3. Stage ③ — Offline evaluation: score every layer separately · 4. Stage ③b — Who does the scoring, and reading the numbers honestly · 5. Stage ④ — The release gate and CI · 6. Stage ⑤ — Production and online evaluation · 7. Stage ⑥ — Human feedback, and closing the loop · 8. The layer above: is the harness itself still working? · 9. The traps, in one table · 10. Build order — what to do first · 11. The one-page card · References |

### `docs/roadmap-explainers/10-the-enterprise-harness-end-to-end.md` — Level 10, The Enterprise Harness, End to End (5,000 words)

| | Covers |
|---|---|
| **Sections** | 1. Write the Contract Before Any Code Exists (Stage ①) · 2. Build the Golden Set, and Know How It Lies (Stage ②) · 3. Score Every Layer Separately (Stage ③) · 4. Choose the Scorer, and Read the Numbers Honestly (Stage ③b) · 5. Wire the Gate Into CI (Stage ④) · 6. Measure Production Without an Answer Key (Stage ⑤) · 7. Close the Loop With Human Labels (Stage ⑥) · 8. Check That the Harness Itself Still Works · 9. Scan the Traps · 10. Build in This Order · 11. Keep the One-Page Card · Key Takeaways · Check Yourself · References |
| **Note** | Every stage produces the artifact the next one consumes, so a skipped stage does not fail — it keeps reporting green while measuring nothing. In the house format: trade-off tagline, reading time, imperative headings, argument-carrying prose, key takeaways and a self-check. The original edition is kept unpublished under `archive/roadmap-explainers-org/`. |

### Folder indexes

| File | What it indexes |
|---|---|
| `docs/README.md` | The five docs subfolders |
| `docs/concepts/README.md` | The three theory companions |
| `docs/guide-audits/README.md` | The two external-guide audits and the tutorial (markdown and HTML), why there are two and not one, and the recount habit |
| `docs/interactive-labs/README.md` | The six labs, the surface map, lab → notebook mapping, the four tools |
| `docs/interview-prep/README.md` | The drill, the question bank, and the shape of a good answer |
| `docs/study-guide/README.md` | The staged study plan — seven stages, time estimates, the fast path — and the basic → expert roadmap |

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
supervisor over four specialists) exists only to be measured. **All 12 notebooks are
complete and run clean end to end.** They hand off through files in `data/` and never import
from each other — the inverse of course 02.

**What costs money:** notebooks 01, 02, 04, 05 and 06 generate live (`gpt-4o-mini`, including
one reply per case in 05), and judged metrics run on `gpt-4.1-mini`. `SCORE_MODE` replays
cached judge verdicts from `data/score_cache/`, so a second run re-judges nothing — `"strict"`
refuses to spend at all and `"record"` re-judges everything. `tests/test_release_gate.py` is
paid on every run.

| Notebook | Covers | Produces |
|---|---|---|
| `01_knowledge_base_and_rag_agent` | 40 multilingual articles, chunking, Chroma, hybrid retrieval, cite-or-refuse | `data/chroma/` |
| `02_tools_agents_and_supervisor_graph` | SQLite ground truth, approval-gated writes, LangGraph, the trajectory dict | `data/lumen.db`, `data/sample_trajectory.json` |
| `03_the_golden_set` | Case anatomy (six expectations, not one), strata, the 20% refusal quota, the datasheet | `data/golden_set.json` |
| `04_rag_evaluation_with_ragas` | RAGAS 0.4 collections API, citation accuracy as a regex vs. a rubric, per-language reporting | `data/rag_report.json` |
| `05_tool_call_evaluation` | Level 1: `ToolCorrectnessMetric`, `ArgumentCorrectnessMetric`, `ok`/`empty`/`unavailable` | `data/tool_report.json` |
| `06_agent_handoff_and_end_to_end` | Levels 2–3: routing confusion matrix, handoff integrity, trajectory matching, SQLite final-state check, blame attribution | `data/agent_report.json` |
| `07_safety_and_policy_checks` | Assertions that block absolutely; why a flaky safety test is a safety problem | `data/safety_report.json` |
| `08_building_custom_judges` | `GEval` vs. `DAGMetric` vs. rubrics; position bias and same-model bias | `data/judge_comparison.json` |
| `09_human_feedback_and_calibration` | Three kinds of human feedback, Cohen's kappa by hand, the rubber-stamp signal | `data/human_labels.jsonl` |
| `10_stratified_reporting_and_statistics` | Sample size, McNemar, bootstrap — stdlib only, no pandas | `data/baseline_report.json` |
| `11_the_release_gate_and_ci` | Four gate checks, four scenarios, `tests/test_release_gate.py`, the two-job workflow | `data/gate_result.json` |
| `12_online_evaluation_and_the_loop` | Reference-free metrics, five alerts, incident drills, canary, closing the loop | `data/online_report.json` |

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
| `rag-evaluation-techniques/` | Three standalone RAG-evaluation notebooks (RAGAS end to end, GroUSE judge meta-evaluation, Open-RAG-Eval nugget metrics) from Nir Diamant's *RAG_Techniques*. Third-party, non-commercial licence kept alongside |
| `agent-evaluation/crewai-travel-planner/` | A real 3-agent CrewAI app used as an evaluation target |
| `agent-evaluation/multi-agent-eval-demo/` | A deliberately tiny LangGraph supervisor + two specialists, scored by checkable metrics and an LLM judge, served by FastAPI with a Streamlit scorecard |
| `langgraph-agent-rag-eval/` | 9-metric trace-level suite, interview-prep framing |

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
the `link-check` skill's `scripts/check_links.py` catches broken links but not a
section reference that has silently become wrong.

A new file under `docs/` needs three registrations, or something fails: a row or section here
(`.github/scripts/check_index_coverage.py`), an entry in `site/build.py`'s `RENDER`, `COPY` or
`SKIP` (the site build's completeness check), and the folder's own `README.md`. The site
redeploys itself from `main`, so once those are in and pushed, it is live at
https://eval-demystified.vercel.app within a minute.
