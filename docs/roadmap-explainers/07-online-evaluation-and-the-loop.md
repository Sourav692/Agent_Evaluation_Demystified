# Online Evaluation and the Loop

*Every check that needs an answer key dies at deployment, and it dies silently, reporting "skipped" rather than failing.*

◷ 22 min read · Level 7 · Assumes Levels 0–6: the five-layer taxonomy, the reference-based split, judges and their failure modes, statistics and stratified
reporting, and the release gate.

Level 6 ended with a gate. A build passes a fixed, curated set of cases, or it does not ship. **That gate can only ever catch what someone thought to put in the dataset.** Production is where the rest arrives.

> **Who this is for.** No library or platform knowledge is assumed. Every technical term is defined in plain words the first time it appears.

Picture the same support agent, now live. None of the following was in the golden set, because the golden set is a claim about what was expected.

- **A question nobody planned for.** It arrives, and nobody wrote a golden case for it.
- **An index that empties silently.** A knowledge-base rebuild returns zero documents while still answering "200 OK".
- **A loop with no error.** A tool starts retrying itself in a loop that never shows up as an error.

Production differs from a golden set in three ways. Every technique here exists because of one of them.

- **The traffic mix is not the suite's mix.** Real traffic is mostly easy and repetitive. A golden set is deliberately hard.
- **There are no reference answers, ever.** Nobody writes them for live traffic.
- **There is a long tail the dataset never represented.** That tail is the reason to do this at all.

> **Stop scoring correctness. Start scoring consistency and shape.** "Is this right?" needs a reference. "Is this grounded in what it retrieved?" and "is this better than the build we shipped?" do not.

---

## 1. Accept That Production Has No Ground Truth

Nobody wrote the correct answer to a question a real customer asked thirty seconds ago. Nobody ever will. That fact splits the suite in two, and a mechanical test draws the line.

> **Does this scorer read an expectation**, such as an expected answer, an expected list of tool calls or an expected final state? **If yes, it is offline-only, however good it is.**

Point an offline-only scorer at live traffic and it does not error. Here is what happens instead.

- **The scorer skips.** A tool-correctness scorer reads an expected tool-call flag. Online it returns "skipped" on every single trace.
- **The dashboard stays green.** The scorer goes dark silently while looking perfectly healthy.
- **Silence looks like good news.** A scorer going dark reads exactly like a scorer reporting good news. That is the failure mode to design against.

| | Runs online? | Why |
|---|---|---|
| Context recall, context precision | ❌ No | Needs the set of documents that *should* have been retrieved |
| Answer correctness vs. a reference | ❌ No | Needs a human-written right answer |
| Tool correctness | ❌ No | Needs an expected tool-call list |
| Faithfulness / groundedness | ✅ Yes | Compares the answer to its **own** logged context; no reference needed |
| Goal accuracy (without-reference form) | ✅ Yes | A judge infers the goal from the conversation itself |
| Topic adherence | ✅ Yes | Scope comes from policy, not from a golden answer |
| Trajectory / safety assertions | ✅ Yes, **on 100%** | Deterministic, reads the trace directly, costs nothing |
| Paired canary comparison | ✅ Yes | Compares one build to another, not to an ideal |

**Everything that needs an answer key dies at deployment**, however well it worked in CI. A three-way split shows the same line from another angle.

| Offline-only | Runs in both | Online-only |
|---|---|---|
| Answer correctness vs. a written reference | Faithfulness / groundedness (context is its own reference) | Deflection rate, escalation rate, reformulation rate |
| Task/tool correctness vs. a known-correct action | Safety & trajectory assertions (approval, tenant isolation) | p95 latency, cost-per-success drift, queue depth |
| Anything scored against a human-authored "right answer" | Citation accuracy, contradiction disclosure | Tool status mix, cache hit rate, corpus/traffic drift |

- **The middle column** holds a different *kind* of check. It never needed a reference in the first place.
- **The right column** holds metrics that do not exist until real traffic does.

**An offline resolution rate and an online resolution rate are never comparable.** Never plot them on the same axis. A golden set is deliberately hard and production is mostly easy. A gap is expected. Watch whether that gap *changes* over time.

---

## 2. Score Consistency and Shape Instead of Correctness

An online judge has no pre-written answer to compare against. Production substitutes for a golden answer in three ways. A fourth technique checks the setup from outside.

- **Self-consistency judges the answer against its own trajectory.** The judge compares the answer to the context *this exact run just retrieved*, which production already logs. The reference travels with the run. No external ground truth is needed. For RAG it is faithfulness, citation accuracy and contradiction disclosure. For a support agent it is whether the reply matched the tool's logged output.
- **Deterministic trajectory rules need no judge at all.** Safety and policy checks were never comparisons to a reference. Did it call the write-tool without an approval step? Did it cross a tenant boundary? Those are pass/fail assertions read off the logged trace. They run online exactly as in the gate, at full volume, for free.
- **Periodic human labels calibrate rather than score.** A small sample goes to reviewers on a delay, in a batch, never inline. The batch measures how well the judge agrees with a human on the *same* case. It also becomes new golden cases, and the offline suite stops describing last quarter's traffic.
- **Some labels arrive on their own, later.** A **delayed outcome** is ground truth that production produces for free. Was the ticket reopened? Did the proposed fix resolve it? Did the customer come back with the same question?
- **A reviewer's verdict is a label too.** When a person reviews an output before it is used, their **accept, edit or reject** is a label with perfect provenance. It is collected as a side effect of the work. Log it and delayed outcomes from day one. Neither needs a labelling budget.
- **A causal claim needs checking against reality.** When an agent reports a root cause, self-consistency only says the claim agrees with what the run retrieved. It cannot say the stated cause produced the failure. Before the report goes out, re-check the claim against a real record. Does the failing row, log line or config actually show what the agent says? Until that check exists, the control is human review before anything acts on the claim.
- **Paired canary comparison is relative.** A **canary** is a new build that gets a slice of live traffic before a full rollout. The question is whether it wins, loses or ties against the old build on the same live input. That needs no ground truth either, only two things to compare.

```mermaid
flowchart TD
    Q{"Does this need a<br/>pre-written correct answer?"}
    Q -->|"Yes"| OFF["Offline-only.<br/>Dies silently in production —<br/>returns 'skip', not an error."]
    Q -->|"No — it can be checked against<br/>its own trace, a fixed rule,<br/>or another build"| ONL["Runs online.<br/>Self-consistency, deterministic<br/>rules, or paired comparison."]
    ONL --> H["Periodic human labels (delayed,<br/>batched) calibrate whichever<br/>judge is doing the scoring."]
    style OFF fill:#EDE3CE,stroke:#9A6A12,color:#0E2226
    style ONL fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

Production reaches for these in a fixed order of preference.

1. **The logged context** stands in for a golden answer wherever it can.
2. **Rule-based assertions** take over where no judgment is needed.
3. **Human labels** come only in small, delayed samples, never to score every request.

Where the tools named across this roadmap help online:

| Tool | What it is good at online |
|---|---|
| RAGAS | RAG-specific metrics; its with/without-reference split says plainly which side of Section 1's line each metric falls on |
| DeepEval | Component-level metrics, `assert_test` in CI, tracing via `@observe` |
| Langfuse | Trace storage, annotation queues and user-feedback scores (the human-label loop above) |
| MLflow / LangSmith | Experiment tracking and trace comparison across builds |

**No off-the-shelf toolkit ships the two things this level depends on: the final-state check and the release gate.** Both stay in-house. Only the team running the system knows what its database should look like afterward. Only that team knows what "good enough to ship" means for that product.

---

## 3. Sample the Judges, Never the Free Checks

Knowing *which* checks can run online leaves a second question. How much of production should each one see? The answer is two different amounts.

- **Never sample the free checks.** Deterministic rules cost nothing per call. Sampling one buys a blind spot for no saving. They run on 100% of traffic, always.
- **Sample only the judges.** Judge-based metrics cost real money per call. At $0.0015 per judged conversation, scoring all 2,000 daily conversations costs roughly $3/day. That is cheap for one agent. It is also the number that gets a sampling policy approved once there are dozens.

**A sampled rate is an estimate, and estimates have error bars.** Grade a 5% sample of 2,000 daily conversations. The pass rate can sit **±4.5 percentage points** either side of the truth, from luck alone. Grade a different 100 tomorrow with nothing changed, and a 2–3 point swing appears. That swing is pure noise.

> **The soup analogy.** One spoonful settles instantly whether the pot is far too salty. It can never settle whether today's pot is 2% saltier than
> yesterday's, especially when it is a different pot every day, which is what a day of production traffic is.

| Sample rate | Traces/day (at 2,000/day) | Resolution (95% CI half-width) | Smallest reliably detectable drop |
|---|---|---|---|
| 5% | 100 | ± 4.5 points | ~9 points |
| 30% | 600 | ± 1.8 points | ~2 points |
| 100% | 2,000 | ± 1.0 point | ~1 point; if even this can't resolve it, the comparison belongs offline |

The resolution column is the **confidence interval half-width**: how far the measured rate can sit from the true rate by luck. This diagram shows how a check gets its sample rate.

```mermaid
flowchart TD
    C{"Is the check<br/>deterministic and free?"}
    C -->|"Yes"| ALL["Run it on 100%<br/>of traffic. Never sample."]
    C -->|"No, it is a judge"| R["Name the smallest<br/>regression worth catching"]
    R --> N["Look up the sample size<br/>that resolves it"]
    N --> P["Price that rate"]
    R -->|"Too small to see<br/>even at 100%"| OFF["Move the comparison offline,<br/>paired on a fixed dataset"]
    style ALL fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

- **Pick the sample rate from the smallest regression worth refusing to miss, not from a round number that felt affordable.** Decide the drop that must be caught, look up the sample size resolving it, then price it. Have that budget conversation before an incident, not during one.
- **An alert set tighter than the resolution fires on noise.** It gets muted within a month. After that the monitoring looks healthy and tells nobody anything. That can be worse than no monitoring, because it still *looks* like monitoring.
- **Know what a delta means before setting a threshold.** A metric named after the failure it detects runs backwards. A rise in it is bad news.
- **If a regression is too small to see even at 100% sampling, do not chase it online at all.** Move that comparison offline. There every input in a fixed dataset gets scored, and the comparison is *paired*.
- **Sample rates are not set once and left alone.** Raise a judge's rate while investigating a complaint, then lower it back. Pause a monitor during a noisy migration without losing its configuration. Delete one once its scorer is superseded.
- **Cost and latency get measured here, and nothing gates on them.** Both appear on these dashboards. Neither blocks a release the way a quality or safety floor does. In production they should. A technically correct answer that takes nine seconds is a failure of a different kind.

---

## 4. Alert on Shape, Not on Quality

Quality judges are sampled and slow. The alerts that page someone are *shape* metrics instead. A **shape metric** counts how the system behaves (cost, citations, tool results, loops), and it needs no answer key. It can run cheaply across all of production.

| Alert | Fires when | Catches |
|---|---|---|
| Cost spike | Cost per conversation exceeds 3× the trailing median | A verbose-prompt regression, a retry loop |
| Citation-free rate | Share of answers citing nothing exceeds a floor | A silently empty retrieval index, a retrieval outage |
| Tool status mix | The share of `empty`/`unavailable` tool results shifts materially | A data source going quietly stale |
| Approval decision time | The median falls below a floor | Rubber-stamping, the signal Level 4 warned about |
| Loop rate | An identical tool call repeats within one conversation | Retry storms, stuck agents |

**The first alert should be a structural one: trace volume, error-span rate, scorer-coverage rate.** Those catch the monitoring pipeline itself silently stopping. Everywhere else, that looks exactly like a healthy system.

**A quality score is the least sensitive thing on a dashboard.** A prompt change making an agent chattier and more hedging moves like this:

| Signal | Before | After |
|---|---|---|
| Quality judge | 0.90 | 0.89 (barely moves) |
| Tool-call rate | 62% | 31% (halved) |
| Mean response length | 140 words | 310 words (doubled) |
| Refusal rate | 3% | 11% (tripled) |

Three of those four moved immediately, and none is a quality score. Four categories are worth watching, and only one is a quality number.

- **Quality on sampled traffic**, as a trend rather than a gate.
- **Behavioural distributions**, like tool-call rate.
- **Operational shape per step**, which turns "it got slower" into "retrieval latency doubled".
- **Failures and refusals.**

> **A rising refusal rate is a quality regression that most quality metrics score as a pass.** The refusal is well-written and safe. Nothing looks
> wrong to a judge reading one turn.

**Adoption is a quality signal, and it can be the earliest one.** When people quietly stop using an output, it may be right but useless. Or it is wrong often enough that checking it costs more than doing the work. Four measures read it without a single label.

| Signal | What it reads |
|---|---|
| Acceptance rate | Share of outputs used as given |
| Edit distance | How far the final text moved from the generated text |
| Time-to-close, with vs. without the tool | Whether the tool actually saves work |
| Quietly ignored outputs | Produced, never opened or acted on |

- **A falling acceptance rate under flat quality scores means the quality scores measure the wrong thing.** They measure correctness, when users needed specificity.
- **Instrument adoption from launch.** Retrofitted, there is no "before" to compare against.
- **Watch the inputs too.** A router forced to choose among known routes picks one, confidently, even for a request it has never seen. A rising rate of low-confidence routing decisions is a drift warning that needs no labels.
- **Give the router an explicit no route / escalate to a human outcome.** Score it as a *correct* answer in its own right. Honest uncertainty then does not count as a failure.
- **A monitor that was configured but never switched on looks exactly like a monitor reporting no problems.** Registering a scorer creates it. Starting it is what begins evaluating. Verifying the pipeline is running belongs on the launch checklist, not in the assumptions.

---

## 5. Drill the Alerts to Learn What They Miss

**An alert nobody has seen fire is an alert nobody knows is wired up.** Break production on purpose. Watch which lights come on and which stay dark.

- **Drill 1, a silently empty retrieval index.** A rebuild returns zero documents for every query. The service still answers with a fluent 200 OK, and an error-rate dashboard sees nothing. Citation-free rate fires almost immediately, because it is a counting rule over data already logged. Resolution rate barely moves. Billing and account questions still "succeed" with no documentation behind them.
- **Drill 2, a retry loop.** A tool starts calling itself repeatedly inside one conversation. Cost and loop-rate fire. Citation-free stays quiet. Resolution rate is unchanged. Customers are helped correctly, repeatedly, at several times the price, and no quality dashboard shows it.

This diagram traces Drill 1 to the dashboards it reaches.

```mermaid
flowchart LR
    R["Index rebuild returns<br/>zero documents"] --> S["Service still answers<br/>a fluent 200 OK"]
    S --> E["Error-rate dashboard:<br/>sees nothing"]
    S --> RR["Resolution rate:<br/>barely moves"]
    S --> CF["Citation-free rate:<br/>fires almost at once"]
    style CF fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

> *"An index rebuild that returns zero rows still returns HTTP success, so error-rate monitoring stays green while quality collapses."*

At larger scale, an upstream service returned HTTP 200 with an empty body during an outage. The model retried with reworded arguments. For eleven hours, 70% of conversations hit the step ceiling.

> **Latency and error rate both stayed green.** What caught the cause was the tool status mix shifting toward `empty`/`unavailable`.

Running every fault against every alert produces a coverage matrix. **Record its gaps instead of hiding them. Finding them is what the drill is for.**

| Incident | Cost spike | Citation-free | Tool status mix | Approval time | Loop rate |
|---|---|---|---|---|---|
| Healthy day | — | — | — | — | — |
| Empty index | — | 🚨 | — | — | — |
| Retry loop | 🚨 | — | — | — | 🚨 |
| Verbose prompt | 🚨 | — | — | — | — |
| Tool source stale | — | — | 🚨 | — | — |

An alert that never fires in any drill is not necessarily useless. The approval-time alert catches rubber-stamping, which none of these drills simulate. But **an alert whose last confirmed firing was during its own code review is decoration.** Run a drill for every alert, on a schedule.

---

## 6. Ask Whether the New Build Beats the Old One

Without a reference, "is this build good?" cannot be asked. The rollout decision rests on a strictly easier question: **is it better than the one already running?**

The mechanism is a **paired comparison**, in three steps.

1. **Split the traffic.** Route a slice of traffic to the new build, and the same slice's inputs to the old one.
2. **Count four buckets.** Both succeeded, only the old one succeeded, only the new one succeeded, both failed.
3. **Test the two "only one succeeded" counts.** They are exactly the paired cells McNemar's test was built for. **McNemar's test** checks whether two systems' pass/fail results on the same inputs differ by more than chance. It is the same statistical question, asked about two live builds instead of two offline runs.

| Result | Verdict |
|---|---|
| Significant, and the new build wins more often than it loses | **Promote** |
| Significant, and the new build loses more often | **Roll back** |
| Not yet distinguishable from noise | **Keep watching** |

```mermaid
flowchart TD
    T["Live traffic slice"] --> N["New build"]
    T --> O["Old build"]
    N --> B["Four buckets: both ok,<br/>only old ok, only new ok,<br/>both failed"]
    O --> B
    B --> M{"McNemar's test on the<br/>two 'only one succeeded' cells"}
    M -->|"Significant, new wins"| P["Promote"]
    M -->|"Significant, new loses"| RB["Roll back"]
    M -->|"Not yet distinguishable<br/>from noise"| K["Keep watching"]
    style K fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

**"Keep watching" is a decision in its own right.** A small canary slice cannot resolve many genuine differences yet. The honest move is to let it keep running rather than promote on a coin flip. Name the regression that cannot be missed. Do not call the race before the sample can call it.

### A/B testing is a different instrument

An **A/B test** shows each variant to a different **cohort**, a separate group of users. The two instruments answer different questions.

| | Paired canary | A/B test |
|---|---|---|
| Question | *Is the new build worse?* | *Which variant do users do better with?* |
| Inputs | The same inputs for both builds | Different cohorts |
| Measured by | Win, lose or tie on each input | Outcomes: task completion, escalation, edits, return visits |

Four rules keep an A/B test honest:

- **Only A/B variants that already passed offline.** Never put a build that fails a safety assertion in front of real users to see what happens.
- **Split cohorts by the strata that matter** (role, workflow, tenant) and report per cohort, for the same reason Level 5 reports per stratum.
- **Wait out novelty.** Early lifts can fade as users get used to a change. Fix the run length before starting, not when the curve looks good.
- **Know the traffic limit.** A low-traffic workflow may never reach a significant result. For those, the paired canary and offline evaluation are the decision, not the A/B.

---

## 7. Turn Every Finding Into a Permanent Test

Every technique above produces a signal. **The signal only compounds if it turns into a permanently harder test suite.** Otherwise a finding helps exactly once, and the next incident starts from zero.

```mermaid
flowchart TD
    A["Production trace"] --> B["Sampled: judge disagreement,<br/>alert-adjacent, unrepresented intents"]
    B --> C["Human label<br/>(the Level 4 calibration step)"]
    C --> D["New golden case,<br/>with strata tags (Level 3)"]
    D --> E["The release gate now blocks<br/>on a failure that once shipped (Level 6)"]
```

**What gets selected for labelling is deliberately not a random sample of healthy traffic.** That would be cheap to label and teach nothing the golden set does not already know. Selection targets where the suite is weakest.

- **Unrepresented intents.** Conversations from intents the golden set has zero examples of.
- **Uncited answers.** Answers with no citation, a shape that can precede a hallucination.
- **Non-ok tool results.** Conversations where a tool returned something other than `ok`.

**A drift check keeps the gate honest about what it protects.** A golden set is a claim about what traffic looks like, and traffic moves. A **stratum** is one slice of cases, such as one language.

- **Measure the gap.** Compare the golden set's stratum mix, say by language, against production's actual mix. Use **total variation distance**: half the sum of the absolute differences between each stratum's share in the two.
- **Set the flag.** The course notebook flags anything above 0.15.
- **Act on drift.** When the two have drifted apart, the per-stratum floors are tuned for a traffic mix that no longer exists. Either rebalance the suite, or accept that a shrinking segment is being over-protected at the expense of a growing one.

**Watch the judge for drift too.** The delayed human labels from Section 2 give a running agreement score between the judge and the reviewers, called **kappa**.

- **Track kappa itself.** Kappa can collapse while raw agreement barely moves. Alert when kappa falls below a floor.
- **Plan for the gaps.** Decide in advance what that alert does on the days no labels have arrived yet.
- **Realign a drifted judge.** It goes back through alignment before its scores are trusted again.

**Every incident ends by adding a golden case.** An incident that does not change the suite will happen again, and the second time nobody will remember the first.

---

## 8. Trace Live, and Judge the Tool's Own Output

Everything up to here builds and scores test cases by hand. That is the right way to *learn* what each check does. Against a live system, every model call, tool call and agent step has to be captured automatically as a **span**, one timed record of one step.

- **Real tracing changes what "the trace" even is.** Instrument every model call automatically. Then wrap explicit spans around the router loop and each tool call. That is the production version of a hand-rolled trace list, captured by infrastructure instead of an append call. Router and tool-selection checks run unchanged against it, queried off real spans.
- **Traces land as queryable data, which has no offline equivalent.** Each span becomes one row in a table, joinable and queryable. Latency can be queried per span type rather than guessed at. A vague "it got slower" becomes a specific "retrieval p95 doubled".
- **Skill evaluation judges a tool's own output quality, in isolation.** Is the SQL a tool generated actually correct? Does generated chart code run? Where possible this is code-based rather than judged: does the generated code execute?

**A well-chosen tool that does its job badly is invisible to every check so far.**

| Check | Result | Why |
|---|---|---|
| Tool selection | Passes | The right tool was picked |
| Argument correctness | Passes | The arguments were valid |
| The tool's output | Quietly wrong | No check read it |

**Version comparison re-runs the same experiment against a changed system.** Every check so far judges one run in isolation. This one re-runs an identical dataset, task and evaluator against a system with one deliberate change. Then it compares the two runs. It answers *"did my prompt change actually help, or did it just feel better?"* That is the paired-canary question, asked offline before anything ships.

```mermaid
flowchart LR
    D["Same dataset,<br/>task and evaluator"] --> A["Run A:<br/>current system"]
    D --> B["Run B: one<br/>deliberate change"]
    A --> C["Compare<br/>the two runs"]
    B --> C
```

The dataset/task/evaluator shape is what makes this generalise. A one-off script works over a single hand-built trace. The same three objects work for any agent and any metric.

---

## 9. Rehearse the Online Questions

**"What can you measure in production that you can't measure offline, and vice versa?"**

The difference is ground truth. Anything reference-free transfers unchanged. Anything needing a written answer key is offline-only, and fails *quietly* online. Offline is total coverage of a narrow fixed world with a hard bar. Online is partial coverage of the real world with only a trend. **The loop between them is not optional.** A production discovery becomes a permanent offline test, or it helps once.

**"You can't afford to judge every production request. How do you sample?"**

Two decisions. The first is where people go wrong, by treating everything as one pool. Never sample the free deterministic checks. Then derive the judge sample rate from the smallest regression that must be detected. Do not use a round, affordable-sounding number. **A rate picked for affordability might be unable to detect anything anyone would act on.** That is the worst outcome, because it still looks like monitoring.

**"What does production monitoring look like beyond a quality score?"**

Four things, and only one is a quality number. Quality on sampled traffic, as a trend. Behavioural distributions like tool-call rate, which drift long before quality does. Per-step operational shape, which turns "it got slower" into a diagnosis. And failures and refusals, since a rising refusal rate is a regression most quality metrics score as a pass. Then check for the monitor configured but never started.

**"Set up production monitoring for a 2,000-conversation-a-day agent."**

The mechanical eligibility test first. Sample the judges and never the deterministic checks. Derive the rate from the smallest detectable drop: roughly 30% to resolve 2 points at this volume. Land traces as queryable tables. Then "it got worse" becomes "retrieval p95 doubled for tenant 14 starting Tuesday". And carry every finding into a gated offline test.

> *"An alert threshold finer than your sampling resolution is a noise generator."*

Verify each scorer has a live sampling config, not just a registration.

---

## Key Takeaways

- Any scorer reading an expectation is offline-only. Online it returns "skipped" rather than failing, and that silence reads as health.
- Production substitutes the run's own logged context for a golden answer, falls back to deterministic rules, and uses delayed human labels only to keep the judge honest.
- Never sample the free checks. Derive the judge's sample rate from the smallest regression worth refusing to miss.
- Alert on shape rather than quality, because a quality score is the least sensitive number on the dashboard.
- An alert nobody has watched fire is an alert nobody knows is wired up, and the coverage gaps are the point of a drill.
- Without a reference the answerable question is whether the new build beats the old one, and "keep watching" is a real verdict.
- A finding only compounds if it becomes a golden case.
- A well-chosen tool doing its job badly passes every selection and argument check. The tool's own output needs judging too.

## Check Yourself

1. Your tool-correctness scorer shows no failures in production for a month. Is the agent healthy? **Unknown. It reads an expected tool-call list, so
   it returns "skipped" on every trace. It went dark, and that looks identical to good news.**
2. Offline resolution is 0.72 and online resolution is 0.91. Which is wrong? **Neither. A golden set is deliberately hard and production is mostly
   easy. Only a change in the gap matters.**
3. Why can faithfulness run online when answer correctness cannot? **Its reference travels with the run: the answer is compared to the context that
   run retrieved, not to a written answer.**
4. A teammate proposes sampling the deterministic safety assertions at 10% to save money. What is wrong? **They cost nothing per call. Sampling buys a
   blind spot for no saving.**
5. You grade 5% of traffic and alert at a 2-point drop. What happens? **It fires on ordinary days, gets muted within a month, and leaves monitoring
   that still looks like monitoring.**
6. An index rebuild returns zero documents and the service answers 200 OK. Which alert fires, and which stays quiet? **Citation-free rate fires.
   Resolution rate barely moves, because questions still "succeed" with nothing behind them.**
7. A canary shows the new build ahead but not significantly. What do you do? **Keep watching. That is a verdict, and promoting on a coin flip would be
   the failure.**
8. Tool selection and argument correctness both pass, and the generated SQL is wrong. What was never checked? **The tool's own output. Skill
   evaluation is the missing check, and it is often code-based rather than judged.**

---

## References

All content above was drawn only from material already in this repository. Nothing here was invented, and no external source was consulted. This page
is the restyled edition of `archive/roadmap-explainers-org/07-online-evaluation-and-the-loop.md`; its content is the same, including that edition's
table of where each named tool helps online (Section 2) and its drift check by total variation distance (Section 7).

**Notebook:**

- `courses/03-agentic-eval-harness/12_online_evaluation_and_the_loop.ipynb`: the eligibility test, the five alerts, the incident drills and coverage
  matrix, the paired canary, the loop back into the golden set, the 0.15 drift threshold, and the judge-drift (kappa) alert exercise.
- `courses/02-databricks-mlflow-evals/` online-monitoring notebooks: sampling policy, the registered-but-never-started trap, and traces as queryable
  tables.
- `courses/01-rag-agent-tool-evaluation/13_Production_Grade_Agent_Eval_Overview.ipynb`: live tracing, router and skill evaluation logged onto spans,
  and the dataset/task/evaluator experiment shape used in Section 8.

**Docs:**

- [`databricks-mlflow-evals.md`, Part 5](../concepts/databricks-mlflow-evals.md#part-5--online-vs-offline) and [Explainer 05, Section
  6](05-statistics-and-stratified-reporting.md#6-buy-the-sample-rate-that-can-see-the-regression): the offline/online split, the sampling-resolution
  table, and the soup analogy (merged there from the retired online-versus-offline page).
- `docs/concepts/customer-support-multi-agent-case-study.md`, §28: online judges without an answer key (self-consistency, rules, delayed labels, the
  paired canary) on a support system.
- `docs/interview-prep/QUESTION_BANK.md`, Part 5 (Q18–Q20) and Case 15: the four questions reproduced in full in Section 9 rather than pointed at.
- `docs/study-guide/evaluation-roadmap.md`: Level 7's topic list and goal statement.
- `docs/study-guide/evaluation-topic-notebook-mapping.md`: Level 7's resource table.

**Limitations.** Written from the repository's own material without running any notebook or calling any API. It does not verify any vendor's
documentation.

---

**Next:** [Level 8, Safety, Adversarial Testing, and Multi-Agent Attribution](08-safety-adversarial-and-multi-agent-attribution.md) · **Previous:** [Level 6, The Release Gate and CI](06-the-release-gate-and-ci.md)
