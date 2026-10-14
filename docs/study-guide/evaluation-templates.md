# Evaluation templates

Four fill-in documents that turn a harness's numbers into something a team can agree on, file
and act on: a **scorecard** for one evaluated build, a **failure-investigation report** for one
broken case, an **acceptance-criteria document** that fixes the bar before results exist, and a
**regression report** comparing a candidate with what is live.

Copy a template into your own repository or document and fill in the empty column. Every
template says when to reach for it, and links to the explainer that teaches the reasoning behind
its fields. A field you cannot fill is a finding in itself: write "not measured" and why,
rather than deleting the row.

---

## 1. Evaluation scorecard

**When to use it.** Once per evaluated build, whether a release candidate, a pilot checkpoint or
a monthly health run. It is the one page every audience starts from. The executive reads the
verdict and the risks, the engineer reads the failing metrics and versions, and the safety
reviewer reads the violations. Fill it in from a single run, so every number on it came from the
same dataset version and the same judge. A scorecard that mixes runs cannot be traced back to
anything.

**Run identity**

| Field | Your entry |
|---|---|
| System and build | |
| Prompt version · model version · retriever / index version | |
| Dataset name, version and content hash | |
| Judge model and rubric version (or "verdicts replayed from cache") | |
| Run date and who ran it | |
| Cases: run / scored / not measured / errored | |

**Results**

| Metric | Target | Blocking? | Result | Interval | Worst stratum (name, score, n) | Pass? |
|---|---|---|---|---|---|---|
| Correctness | | | | | | |
| Groundedness | | | | | | |
| Retrieval recall at the cut-off used | | | | | | |
| Tool-call correctness | | | | | | |
| Task completion / final-state check | | | | | | |
| Answer-quality dimensions (helpfulness, completeness, tone, …) | | | | | | |
| Latency p50 / p95 | | | | | | |
| Cost per answer | | | | | | |

**Safety and verdict**

| Field | Your entry |
|---|---|
| Safety violations, listed as case IDs (never a rate) | |
| Verdict: ready / not ready / ready with named exceptions | |
| Readiness against target, in one sentence | |
| Top three risks | |
| Next actions, each with an owner and a date | |
| Known gaps: not measured, why, and the compensating control | |

**Taught in:** [Level 9 §4](../roadmap-explainers/09-the-harness-as-a-product.md) (the core
metrics, their four tags, and the executive summary) ·
[Level 5](../roadmap-explainers/05-statistics-and-stratified-reporting.md) (intervals, and
reporting the worst stratum) ·
[Level 8 §1](../roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md)
(safety as a list) · [Level 4](../roadmap-explainers/04-judges-and-the-humans-who-validate-them.md)
(the answer-quality dimensions).

---

## 2. Failure-investigation report

**When to use it.** For one failure worth understanding: a production incident, a failed golden
case, a customer's "this answer is wrong", or a gate that blocked for a reason nobody expected.
The report has two jobs. It finds the *first* thing that broke, rather than the loudest symptom,
and it makes sure the failure becomes a regression case so it cannot come back unnoticed. A
failure fixed without a new case is a failure that will be found again.

**What happened**

| Field | Your entry |
|---|---|
| Failure ID, date, and who reported it | |
| The exact input (and the conversation so far, if multi-turn) | |
| Expected behaviour, and who decided it (provenance) | |
| Actual behaviour | |
| Trace or run link | |
| Versions: prompt · model · retriever / index · dataset · judge | |
| Who was affected, how many, and how badly | |

**Investigation checklist**

- [ ] Reproduced on the same versions, or marked as not reproducible with what was tried
- [ ] Retrieval: was the right evidence retrieved, and did it survive ranking and filtering?
- [ ] Context: did the evidence reach the prompt, and in a usable position?
- [ ] Generation: re-run with the correct evidence supplied by hand. Does the answer come right?
- [ ] Tools: right tool, right arguments, and was the tool's own output read correctly?
- [ ] Routing and handoff: right specialist, required fields intact across every hop?
- [ ] Final state: does the system of record match what the case demanded?
- [ ] Measurement: is the label right, and is the judge calibrated for this kind of case?

**Cause and closure**

| Field | Your entry |
|---|---|
| First broken layer (the first box above that failed) | |
| Root cause, with the evidence | |
| Fix | |
| Regression case added: ID, dataset, version | |
| New scorer or gate entry needed? (a scorer with no gate entry blocks nothing) | |
| Owner and date closed | |
| Prevention: what would have caught this earlier | |

**Taught in:** [Level 8 §3](../roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md)
(blame attribution and its fixed walking order) ·
[Level 2](../roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.md) (tool,
trajectory and final-state checks) ·
[Level 1](../roadmap-explainers/01-rag-retrieval-and-generation.md) (separating retrieval
from generation) · [Level 3 §6](../roadmap-explainers/03-ground-truth.md) (promoting a
production failure into the gated set).

---

## 3. Acceptance-criteria document

**When to use it.** Before the pilot ends, and ideally before the build starts. This is where the
people accountable for the system agree what "good enough to launch" means. Fill it in *before*
any results exist, because criteria fixed in advance are a standard and criteria written after
the results are a rationalisation. Once signed, it is the source the release gate's thresholds
come from. Changing a threshold means changing this document and signing it again.

**Scope**

| Field | Your entry |
|---|---|
| Business objective, and the outcome it should move (deflection, handle time, …) | |
| Use case: what is in scope, and what is explicitly out | |
| Target users and channels | |
| The dataset that measures this: name, version, size, strata | |

**Criteria**

| Criterion | Threshold | Blocking at launch? | Applies to (single-turn, multi-turn, a named stratum) | Owner |
|---|---|---|---|---|
| Correctness on the top request types | | | | |
| Groundedness / approved source cited | | | | |
| Safety and access tests | 100% | yes | | |
| Smallest stratum allowed to block | | | | |
| Latency (p50 and p95) | | | | |
| Cost per answer or per conversation | | | | |

**Operating rules**

| Field | Your entry |
|---|---|
| Must-never-happen list (zero tolerance, each a deterministic check) | |
| Human escalation rules: when the system must hand off | |
| Launch criteria: every blocking row above, plus anything else | |
| Rollback criteria: what triggers it, and who can pull it | |
| Residual risks accepted, and who accepted each one | |
| Known gaps: not measured, why, and the compensating control | |

**Sign-off**

| Role | Name | Date | Version signed |
|---|---|---|---|
| Business owner | | | |
| Security / compliance | | | |
| Data owner | | | |
| Technical owner | | | |

**Taught in:** [Level 9 §3](../roadmap-explainers/09-the-harness-as-a-product.md) (deciding the
bar before the code, and keeping must-have separate from blocking) and §4 (why a threshold
nobody agreed to is an opinion) ·
[Level 6](../roadmap-explainers/06-the-release-gate-and-ci.md) (how the gate enforces it) ·
[Level 8 §6](../roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md) (what a
regulator asks to see).

---

## 4. Regression report

**When to use it.** Every time a candidate is compared against the live baseline: a prompt edit,
a model upgrade, a retriever or index change, a new tool. It answers one question: *is the
candidate at least as good as what is live, everywhere that matters?* Run both sides on the same
cases, so the comparison is paired, and change one thing at a time where you can. A report
comparing two builds on two different datasets measures the datasets.

**What changed**

| Field | Your entry |
|---|---|
| Baseline: prompt · model · retriever / index versions | |
| Candidate: prompt · model · retriever / index versions | |
| The change, in one sentence | |
| Dataset name and version (identical on both sides) | |
| Judge and rubric version, and whether verdicts were cached | |
| Cases compared (paired) | |

**Deltas**

| Metric | Baseline | Candidate | Delta | Interval or paired test | Real change? | Gate |
|---|---|---|---|---|---|---|
| Correctness | | | | | | |
| Groundedness | | | | | | |
| Tool-call correctness | | | | | | |
| Task completion / final state | | | | | | |
| Latency p95 | | | | | | |
| Cost per answer | | | | | | |
| Worst stratum (name) | | | | | | |

**Case-level evidence**

| Field | Your entry |
|---|---|
| Cases that flipped pass → fail (IDs) | |
| Cases that flipped fail → pass (IDs) | |
| New safety violations (IDs; any one blocks) | |
| Strata below their floor | |

**Decision**

| Field | Your entry |
|---|---|
| Ship / do not ship / canary first | |
| Reason, citing the rows above | |
| Who decided, and any override with its justification | |
| Follow-ups: new cases or gates this comparison showed were missing | |

**Taught in:** [Level 5](../roadmap-explainers/05-statistics-and-stratified-reporting.md) (paired
comparison, intervals, whether the suite could see the change) ·
[Level 6](../roadmap-explainers/06-the-release-gate-and-ci.md) (threshold *and* no-regression,
and the four checks) · [Level 9 §1](../roadmap-explainers/09-the-harness-as-a-product.md)
(why an uncached, drifting judge turns every delta into a false alarm) ·
[Level 7](../roadmap-explainers/07-online-evaluation-and-the-loop.md) (the canary that follows a
passed gate).
