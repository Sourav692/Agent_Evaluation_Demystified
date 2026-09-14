# RAG, Agent & Tool Evaluation — Field Guide

Companion to the 14 notebooks in [course 01](../../courses/01-rag-agent-tool-evaluation/). The notebooks show how to express each idea in a framework; this covers the idea.

- **Tool-agnostic on purpose.** No class names, no constructor arguments. Framework APIs churn; the questions don't.
- **Built for recall under pressure.** Bullets and tables over prose. Each check is framed the same way — what it catches, what it misses, what it needs, when to reach for it.
- **Read Part 0 first.** It's the map. After that, jump to whatever you're working through.

**If you have ten minutes:** 0.1, 0.2, 0.3, then 2.3 and Part 3.

---

# Part 0 — The Map

## 0.1 What you can evaluate

"Evaluate the RAG system" is never one question. It's five narrower ones — **retrieval, generation, tool mechanics, trajectory, outcome** — each with its own failures and its own checks. Name the layer before picking anything: a grounding failure and a retrieval failure look identical from outside, and the fixes are unrelated.

**RAG, by pipeline stage:**

| Stage | Question | Failure it catches | How it's measured |
| --- | --- | --- | --- |
| **Retrieval** | Did we fetch the right chunks? | Irrelevant, missing, or badly-ranked context | Precision@K, Recall@K, MRR, nDCG with labels; judged contextual checks without |
| **Generation**, no answer key | Is the answer grounded in what we fetched? | Invented claims on top of correct context; answering a different question | Faithfulness, answer relevancy |
| **Generation**, against an answer key | Is the answer *correct*? | Grounded-but-wrong, because the context itself was wrong | Correctness against a written reference; semantic similarity as a cheap proxy |
| **End-to-end** | Does the pipeline hold up across many queries? | All of the above, in aggregate | Golden dataset + full suite, sliced by category |

**Agents, by behaviour:**

| Behaviour | Question | Failure it catches | How it's measured |
| --- | --- | --- | --- |
| **Tool selection** | Right tools? | Wrong tool, missing tool, tool called when none was needed | Comparison against an expected set; coverage over a trace |
| **Arguments** | Right arguments? | Right tool, malformed or wrong arguments | Schema validation, then judged appropriateness |
| **Trajectory** | Was the *path* sound? | Redundant calls, wasted steps, blind retries | Step-wise accuracy, redundancy, recovery rate, fuzzy match |
| **Task completion** | Did it get the job done? | Every call correct, one stated constraint silently dropped | Judged completion; end-state verification |
| **Conversation** | Does it hold up across turns? | Forgetting earlier turns, drift, acting without consent | Per-turn relevance, knowledge retention, whole-dialogue rubric |

**The shape to remember:** mechanics → process → outcome. Right tool with right arguments doesn't mean a sound sequence; a sound sequence doesn't mean the user's goal was met. Evaluate all three.

## 0.2 The two questions that decide everything

**Question 1 — to run this check, do I need an answer key written in advance?**

A *reference* is a correct answer a human wrote down before the system ever ran — an expected answer, an expected chunk list, an expected tool list. Every check compares the output to something; the only question is where that something comes from.

| The check compares the output to… | It's called | Examples |
| --- | --- | --- |
| Something a **person wrote before the run** | **reference-based** | Recall@K needs a list of which chunks are the right ones. Tool-selection needs the expected tool list. Correctness needs the expected answer. |
| Something the **run itself produced** | **referenceless** | Faithfulness compares the answer to the context just retrieved. Answer relevancy compares the answer to the question. Nobody wrote anything ahead of time. |

- **Reference-based** — precise, gateable, great for CI. Someone has to write and maintain the answer key, so it only scales to curated test sets.
- **Referenceless** — scales to any traffic at zero labeling cost. Less precise, and only as good as the judge.
- **Why this decides offline vs online:** in production a real user asks something nobody anticipated, so no answer key exists for it. A reference-based check has nothing to read and can only **skip** — reporting skip on 100% of traffic while looking perfectly healthy on a dashboard. A referenceless check has everything it needs, because both sides of its comparison came out of that same request.
- **So the test is mechanical:** does it need an answer key? If yes, it can never go online, however good it is. That one question sorts your whole suite before you write a line of code.
- **Mature setups run both** — reference-based in CI, referenceless on live traffic. Not a choice between them.

**Question 2 — deterministic or judged?**

- **Deterministic** = arithmetic or a schema check. Free, instant, reproducible.
- **Judged** = a model reads the output and scores it. Handles open-ended text; costs a call; moves on its own.
- **Reproducibility is the reason, not cost.** When a deterministic number moves, behaviour moved. A judged number needs a tolerance band and can never certify the thing it was used to optimise.

## 0.3 LLM-as-judge — the failure modes

The only practical way to score open-ended text. Not an oracle. Treating it like one is the most common mistake in eval work.

- **Judge capability** — a weaker judge produces noisier scores. It must be at least as capable as the task, sometimes more than the system it grades.
- **Non-determinism** — two runs on the same input can disagree, especially near the threshold. Treat one score as a noisy estimate, not a fact. Never gate on a single row.
- **Rubric sensitivity** — a vague criterion produces a judge that quietly disagrees with itself. The specificity you write down is the specificity you get back.
- **Cost compounds** — five dimensions over 500 cases is 2,500+ calls. This is why the answer-key question in 0.2 is an operational decision, not just a conceptual one.
- **Nobody validates the validator** — an unchecked judge gives numbers that are internally consistent and externally unvalidated. Useful for detecting *change*, not for asserting *quality*.
- **Measure agreement, not average** — a judge that rates everything highly scores beautifully and is useless.
- **Fluent-but-wrong fools it** — it reads text and decides whether it *sounds* right. This is the whole argument for end-state verification.
- **Score direction is not a convention** — a check named for the failure it detects runs backwards: a hallucination score of 0.9 means *lots* of hallucination, not excellent grounding. Check the direction before wiring anything to a threshold.

## 0.4 The cost ladder — pick the cheapest thing that answers the question

| # | Rung | Who writes the standard | What it reads | Cost |
| --- | --- | --- | --- | --- |
| 1 | **Deterministic check** | Nobody — it's arithmetic, a regex, a schema | The specific field it checks | Free, instant, reproducible |
| 2 | **Off-the-shelf judged check** | Someone else — a standard rubric | The final output, plus the question and context | One call, small prompt |
| 3 | **Custom rubric** | You | The final output, plus the question and context | One call, small prompt + your authoring time |
| 4 | **Trace-based judge** | You | The **whole run** — every step, tool call, intermediate reasoning | One call, **big** prompt. A trace is many times the size of an answer |

**Rungs 2, 3 and 4 are all judged.** What separates them is two different things, and it's worth knowing which jump you're making:

- **2 → 3 changes the standard, not the mechanism.** Same evidence, same cost per call. You climb only because the generic definition of "good" isn't yours — a stock "is this complete?" can't know your answer needs a budget breakdown and a day-by-day itinerary.
- **3 → 4 changes the evidence, and it's the expensive jump.** Make it only when **the answer isn't in the output**. "Did it take a sensible path?", "did it recover from that error?", "did it ask before writing?" — no rubric can extract those from the final text, however well written. The judge has to see the run.

**Stop at the first rung that answers your question.**

- **The common overspend is rung 4 for a rung 1 question.** Most trace questions need no judgment at all: redundant calls, cycles, step counts, error-then-retry patterns are all countable. Paying a large-prompt judge to count duplicate calls is the most common way teams waste evaluation budget.
- **Rung 4 is for trace questions that genuinely need judgment** — whether a sequence was reasonable given an ambiguous request, say. Not for anything you could write a query for.
- **The other common overspend is rung 3 for a rung 1 question** — a judged check for something a regex settles.

## 0.5 A note on frameworks

Several evaluation frameworks appear across the notebooks. The only durable fact about them is that they come in two shapes:

- **Metric libraries** — ready-made, named measurements. Fast to start; the naming does some thinking for you, right up until you need a check nobody shipped.
- **Platforms with primitives** — a scoring function, a custom judge, a trace to read. More boilerplate, more flexibility, and usually paired with versioned runs, a trace store, and version comparison.

Every concept here exists in all of them under some name. None of them lets you skip deciding which question you're asking.

---

# Part 1 — RAG Evaluation

## 1.1 Retrieval, with labels (deterministic)

Needs a labeled eval set — query → relevant chunk IDs — and arithmetic. No judge, no API call. The right first move whenever you have labels.

| Measurement | What it checks | Use when |
| --- | --- | --- |
| **Precision@K** | Of K retrieved, how many are relevant | Noise in the retrieved set is the worry |
| **Recall@K** | Of all relevant chunks, how many made the top K | Missing evidence is the worry |
| **MRR** | 1 / rank of the first relevant hit | One correct chunk, and you care how early it lands |
| **nDCG** | Graded relevance, discounted by position | Relevance isn't binary and several relevant chunks coexist |

- **Needs:** pre-labeled ground truth.
- **Misses:** anything on live traffic — you can't compute Precision@K on a query with no labels.
- **That gap is what 1.2 exists to close.**

## 1.2 Retrieval, without labels (judged)

Same question as 1.1, judged instead of labeled. Three checks, three different failures — which is why one general "is retrieval good" score doesn't exist.

| Check | Question | Needs a reference? | Catches |
| --- | --- | --- | --- |
| **Contextual precision** | Are relevant chunks ranked above irrelevant ones? | Yes | A good chunk buried under noise |
| **Contextual recall** | Does the context cover everything the answer needs? | Yes | The retriever found *something*, not *enough* |
| **Contextual relevancy** | How much of what came back is on-topic? | No | Noise diluting the context |

- **Precision cares about order. Recall cares about coverage. Relevancy cares about signal-to-noise.** A retriever can fail one and pass the other two.
- **Note:** contextual recall checks against the *expected* answer, not the generated one — did retrieval fetch enough to support a full answer, regardless of what the generator used.

## 1.3 Generation, without a reference

Given what was retrieved, is the answer any good — with no hand-written reference. These are the checks that can run on production traffic.

| Check | What it compares against |
| --- | --- |
| **Answer relevancy** | The question only — does it address what was asked? |
| **Faithfulness / groundedness** | The retrieved context — any invented claims? |
| **Hallucination vs trusted context** | A separately-supplied trusted source, regardless of retrieval |

**The three ways "the answer is wrong" can happen — learn to tell them apart:**

- **Faithful but irrelevant** — perfectly grounded, answers a different question.
- **Relevant but unfaithful** — addresses the question, invents facts.
- **Faithful to bad context** — accurately reflects chunks that were themselves wrong. **Faithfulness cannot catch this.** Only 1.4 can.

**Faithfulness vs hallucination — the distinction people get wrong:**

| <br> | Faithfulness | Hallucination vs trusted context |
| --- | --- | --- |
| **Compares against** | Whatever *this* query's retriever happened to fetch | A curated trusted source, independent of retrieval |
| **Changes per query?** | Yes — the baseline moves with retrieval | No — the baseline is fixed |
| **Catches** | A generator inventing things beyond what it was given | An answer that contradicts known truth, however it got there |
| **Blind to** | Retrieved context that was itself wrong | Nothing retrieval-specific — it never looks at retrieval |
| **Needs** | Nothing extra; runs on live traffic | A maintained trusted corpus |
| **Reach for it when** | You want to police the generator | You have independent truth and want to police the answer |

## 1.4 Generation, against a reference

- **There's rarely a generic correctness check you can drop in**, and that's not an oversight — what counts as "right" is specific to your task. Write a rubric (1.5).
- **Semantic similarity** (embedding distance to the reference) is cheap and fast, but measures *topical* closeness, not *factual* agreement. Two answers can be close and disagree on the number that matters. Pair it with a judged check; don't substitute it.
- **Needs:** a written reference answer. That's the cost side of 0.2 — precise, and only as scalable as your ability to keep references current.

## 1.5 Writing a rubric that works

**You are either writing the test, or letting the judge write it for you.**

| You give it | What happens | Result |
| --- | --- | --- |
| **One sentence** — "check the answer is accurate" | The judge has to invent the steps, and invents different ones each run | Same answer, different scores |
| **Explicit steps** — "1. every figure appears in the context, 2. it answers the question asked, 3. no advice beyond the policy" | The judge follows yours | Same answer, same score |

- **Write the steps whenever a one-liner doesn't pin down what should fail.** Steps also let you check several things at once — relevance, agreement with the reference, and grounding — in one pass.
- **A vague rubric never errors.** Nothing goes red. You just get numbers that wobble, with no signal saying the rubric is the cause.
- **The test:** if you can't say what would make it fail, neither can the judge.

Same idea as handing a grader "mark this fairly" instead of a marking scheme. Five graders, five different marks, every one of them defensible.

## 1.6 Evaluation inside the pipeline

Everything above scores after the fact. Relevance and grounding can also run *as pipeline steps*: `retrieve → judge context relevance → generate → check faithfulness`.

- **You can branch on it.** Nothing relevant retrieved? Ask a clarifying question instead of generating a plausible answer from noise.
- **It de-mystifies the checks.** Building grounding out of raw judge calls once makes it obvious what a ready-made version is doing underneath.
- **Prototype against mocked judges first.** Same structure, byte-identical output, zero cost. Swap in real judges once the shape is right — and that swap is where non-determinism becomes visible.

## 1.7 Running it in batch

One scored example teaches you what a check does. It says nothing about your system. The step between is always the same shape:

> dataset of inputs → call the **live** system once per row → score the real response → write the score back beside its input

- **Every row hits the live system** — you're testing what's deployed, not a reconstruction.
- **Scores land next to inputs** — a bad number is one click from the input that caused it. That's the difference between a dashboard and a diagnosis.
- **It re-runs on demand** — the prerequisite for comparing a change against what's live.
- **A standard test runner gets you this cheaply** — parametrize over rows and inherit batch execution, pass/fail reporting, and CI.

## 1.8 Golden datasets

- **Hand-writing references doesn't scale** past a handful of examples.
- **Generate them from your own documents** — question/expected-answer pairs, evolved along dimensions you choose (multi-step reasoning, multi-chunk).
- **Spot-check them.** Generated questions are only as good as the generation process.
- **Build each case's context by actually running the retriever** on the golden question — not from the documents the golden came from. Otherwise you're testing whether the generator works given perfect context, which nothing in production ever has.

## 1.9 Reading the results

- **Diagnose by pattern, not by the headline number.** Low contextual precision, high everything else → a ranking problem. Low faithfulness, high contextual relevancy → the generator inventing things despite good retrieval.
- **Aggregates hide the thing you need to see.** 85% with one category at zero and 85% spread evenly are different systems with the same score.
- **Slice before you conclude** — by query category, tenant, intent, document type.

---

# Part 2 — Conversation, Tools & Task

## 2.1 Multi-turn conversation

A system can be fine turn-by-turn and fail as a conversation. The unit of evaluation becomes the sequence.

**What to measure:**

- **Per-turn relevance** — is this turn relevant to what came before it? Judged over a sliding window (the last few turns) rather than the whole dialogue, so a long conversation doesn't drown the check.
- **Knowledge retention** — does it remember what the user said three turns ago? The most visible multi-turn failure is re-asking for something already supplied.
- **Whole-dialogue rubric** — your domain criterion applied across the arc, not one turn.

**The arithmetic nobody does:**

- **Turn pass rates multiply.** If each turn independently passes 95% of the time, a 5-turn conversation passes 0.95 × 0.95 × 0.95 × 0.95 × 0.95 — that is, *p* to the power of the number of turns.
- **So 95% per turn is 77% conversation success**, not 95%.
- The overstatement grows with length — so the metric looks best exactly where the product is worst.
- **If you report turn-level numbers, report the session-level number beside them.**

**Failures with no single-turn representation:**

- **Consent lives between turns.** "Acted without asking" is a property of a pair, not a turn.
- **Approval has three outcomes, not two** — complied, violated, and *stalled* (agreed, then nothing happened). Different fixes.
- **A conversation-level check on a single-turn run must report "not measured", never zero.** An unmeasured check and a failed one must never look alike.

**Scaling past hand-written dialogues:** a simulated user with a goal and a policy — including mid-conversation curveballs — generates dialogues from defined intents, and the same checks score whether the goal was met.

## 2.2 Tool use

**Why it's different from standard evaluation:**

| <br> | Standard LLM evaluation | Tool-using agent evaluation |
| --- | --- | --- |
| **What you score** | One output against a reference | A sequence of decisions, then the output |
| **Where failure lives** | In the text | Underneath it — which tool, what order, what arguments, how results were read |
| **What a good-looking answer proves** | Usually that it's good | Nothing. "Your flight is booked!" is useless if the booking API was never called |
| **Number of failure points** | One | One per decision, each needing its own check |
| **Typical miss** | Wrong wording | A skipped lookup with the details invented to cover it |

**Three checks, three granularities:**

| Check | Scope | Needs an answer key? | Question | Best for |
| --- | --- | --- | --- | --- |
| **Tool selection** | One run | Yes — the expected tool set | Do the tools called match the expected set? | CI, where correct behaviour is known |
| **Argument correctness** | One run | No — judged from the task | Were the arguments right for the task? | Production, where values can't be predetermined |
| **Multi-turn tool use** | Whole dialogue | Partly — selection needs one, arguments don't | Selection *and* arguments across a conversation | Chatbot agents where tool use spans exchanges |

**Four properties worth carrying around.** Running example: a travel agent that should call
`search_flights`, then `book_flight`.

**1. "Did it call the right tools?" has more than one right answer — and you have to pick one.**

How strictly you match is a decision, and both extremes are wrong:

- *Too strict* (exact tools, exact order, nothing extra): the agent also calls `check_weather`,
  which harmed nobody, and you fail the whole run. Nothing went wrong but the score says it did.
- *Too loose* (the expected tools appear somewhere, extras fine): an agent that calls all eight
  of its tools on every question passes every time. It is spraying, and your metric applauds.

Demand strict ordering only where the order genuinely *is* the requirement. You cannot book
before you search, so that ordering is real. Whether the weather lookup came first or third is not.

**2. Check arguments in two passes, cheap one first.**

"Were the arguments right?" is really two different questions:

- *Is it even well-formed?* Does the `book_flight` call have a `date` field, and is `2026-02-31`
  a real date? **Plain code answers this** — free, instant, same answer every time.
- *Does it make sense for what was asked?* The user wanted a morning flight to Delhi; did it
  book an evening flight to Dubai? **Only a judge can answer this.**

Run the code check first and stop there if it fails. Paying for an LLM call to decide whether a
malformed date is *semantically appropriate* is money for nothing.

**3. Combining sub-scores: take the worst one, not the average.**

Suppose tool selection scores 1.0 and arguments score 0.0 — it picked exactly the right tool and
handed it nonsense. The mean says **0.5**, which reads as "half working". Nothing was half
working: the booking failed. The minimum says **0.0**, which is the truth.

Averaging lets a healthy dimension cover for a broken one — precisely the failure you built the
metric to catch.

**4. Doing nothing is behaviour, and it needs scoring too.**

"What's your refund policy?" should produce **no tool call at all** — answer from knowledge and
stop. That restraint is correct, and it deserves a pass.

Most suites only inspect calls that actually happened, which leaves them blind in both directions:

- **Should have stayed still, and moved.** It calls a tool it didn't need — wasted money, one more
  thing to go wrong. Invisible, because you only score whether calls were *correct*, and it was.
- **Should have moved, and stayed still.** It says "your flight is booked!" without ever calling
  `book_flight`. Invisible, because there is no call to inspect.

So the expected tool set has to be allowed to be **empty**, and an empty set has to be something
you can pass or fail against.

## 2.3 Task completion

The checks above judge **mechanics**. None of them ask what the user cares about: **did it get the job done?**

- **The gap is real.** An agent can call every tool correctly and book the wrong hotel because it ignored a stated budget.
- **It runs the other way too.** A slightly inefficient sequence can land on a perfectly good outcome.
- **A production suite needs both.** They answer different questions.

**Judged task completion — how to get it right:**

- **Show it the tool calls**, not just the final output. That's what lets the judge see *how* the outcome was reached rather than what the agent claims.
- **State the task explicitly** rather than letting it be inferred from the raw input. The real requirement is usually richer than the literal wording.
- **A full trace beats a flat call list** where one exists — it carries intermediate reasoning.

**Two escalations:**

1. **When "done" is domain-specific** → custom rubric. "The summary must cite two sources." "A refund response must never promise an amount before a policy lookup." Costs more to write; applies your bar instead of a generic one.
2. **When stakes are high** → **verify the side effect, don't judge the text.** A judged check still only reads text and decides whether it *sounds* done. For agents that book, send, or write, query the system of record directly. This cannot be fooled by a fluent-but-wrong answer.

**In practice, combine them:** deterministic state check as the pass/fail gate wherever a checkable outcome exists; judged check as a secondary signal for the fuzzy parts (tone, completeness of an explanation).

## 2.4 Failure mode — polite tool failure

The single most under-tested failure in production agents, and the one worth being able to walk through end to end:

- **What it means:** a tool returns a soft failure object — `found: false`, an empty result, a 200 with an empty payload — instead of raising.
- **Why it causes a wrong answer:** the model gets something that *looks* like data, skates past it, and fills the gap with fluent, plausible, wrong content.
- **Symptoms:** an agent states a plan and balance for an account that doesn't exist. Nothing crashes. Nothing alerts. Silence and success look identical.
- **Why standard checks miss it:** grounding compares the answer to *retrieved documents*, not tool outputs. Task success reads the final string. **Neither one reads the tool result.**
- **How to detect it:** a deterministic check that reads the tool output and, if it indicates failure, asserts the response doesn't state the facts that tool was supposed to supply.
- **Fix:** make soft failures loud at the tool layer where you control it, and make "I couldn't retrieve that" an explicitly rewarded behaviour in the rubric.
- **Not fixable by prompting.** Instructions reduce the rate; they don't make it detectable.
- **Where else it shows up:** empty retrieval results, a permission-filtered search returning zero rows, a rate-limited call returning a stale cached value.

## Part 2 quick lookup

| Question | Reach for |
| --- | --- |
| Right tools, against a known reference? | Reference-based selection comparison |
| Right arguments, no reference available? | Schema validation, then a judged check |
| Appropriate tool use across a conversation? | Conversational tool use — minimum of selection and arguments |
| Did it accomplish the goal? | Judged task completion, or a custom rubric |
| Did the real side effect happen? | End-state verification against the system of record |
| Did a tool fail quietly and get papered over? | Deterministic check reading the tool output |
| Did it correctly do nothing? | Score the absence of a call as an outcome |

---

# Part 3 — Trajectory

Part 2 scores a **finished** interaction. This asks whether the *path* was any good. An agent can reach the right answer in twice the steps, retry blindly instead of correcting, or repeat an identical call for nothing — and no Part 2 check sees any of it.

**The standard approach:** run the agent's loop to build a **trace** — a step-by-step record of what was called, with what arguments, and what happened — then hand that trace to a **separate** evaluation pass, scored against a **gold trajectory**: the sequence a human decided ahead of time was correct. The agent doesn't grade itself.

*Gold* throughout this part means "the human-authored correct version" — the answer key of 0.2, applied to a path instead of an answer.

## 3.1 The nine checks

| # | Check | What it catches |
| --- | --- | --- |
| 1 | **Tool selection accuracy** | Coverage only — does the called set include the gold set? Loosest of the nine; passes with wrong order and extra calls |
| 2 | **Argument correctness** | Right tool, invalid arguments |
| 3 | **Redundant calls** | A tool-and-arguments pair that already *succeeded* earlier in the same trace |
| 4 | **Step-wise accuracy** | Fraction of all steps that made real forward progress |
| 5 | **Task success rate** | The ground-truth outcome for the run |
| 6 | **Trajectory match (fuzzy)** | Successful tool set vs gold set, ignoring order and retries |
| 7 | **End-state verification** | Read the mutated system of record directly |
| 8 | **Recovery rate** | After an error, did a later step call the same tool and succeed? |
| 9 | **Cost / efficiency proxy** | Redundant calls and errors treated as waste |

## 3.2 Three traps

- **The tool-selection scorer that scores 100% for calling everything.** The commonly published version computes both missing and unexpected tools, then bases the verdict only on the missing ones. **Fail both directions** — an unexpected account lookup is a privacy problem, not an inefficiency.
- **Exact-sequence matching as the default.** It fails on a mid-trace typo or a harmless extra lookup even when the agent did the right things. Fuzzy by default; exact only where order *is* the requirement.
- **Rewarding recovery on its own.** A high recovery rate is genuinely good — an error caught and corrected is a different system from one that fails silently. But pair it with step-wise accuracy, or you're rewarding a system that generates errors so it can recover from them.

## 3.3 What each check looks like on a live system

Hand-computing these from a hand-built trace is how you learn them. On a running system the questions don't change — only where the answer comes from. Take a **support agent that looks up an account, checks network status for a region, and opens a ticket**:

| Question | Where the answer comes from |
| --- | --- |
| Did it call the tools it needed? | Gold set in a table beside the eval questions; called set from tool spans tracing already captures |
| Were the arguments valid? | Typed tool signatures reject malformed calls before execution — the failure never reaches evaluation |
| Did it repeat itself? | Query the trace store for duplicate tool-and-input spans inside one request. Pure SQL, no judge |
| Did each step make progress? | A per-step scorer walking each trace's spans, run as part of the eval job |
| Did the task succeed? | An eval set of task and expected outcome, run on a schedule, trended |
| Was the path close to gold? | Gold trajectories stored as structured data; a comparison function registered once |
| Did the real effect happen? | Before/after diff of the system-of-record table, same run as the agent |
| Did it recover? | Tracing marks error spans; a job matches them against later successful spans in the same tree |
| What did it cost? | Tracing captures tokens and latency per span automatically |

**Three lessons that outrank any row:**

- **Instrumentation is a precondition, not a detail.** An untraceable agent is unevaluable. Every request must emit a span per retrieval, per model call, per tool call, with tokens and latency.
- **Span type is a contract, not a label.** A grounding check *hard-requires* a span typed as a retrieval. Wrong type doesn't degrade the measurement — it breaks it.
- **Queryable traces change incident response.** "It got worse" becomes "retrieval p95 doubled for one tenant starting Tuesday."

---

# Part 4 — Production

## 4.1 Offline and online split cleanly

- **Offline catches what your dataset contains.** Reproducible, can use references, can gate a release. Structurally blind to anything nobody thought to include.
- **Online exists to find what the dataset didn't.** Real traffic has no answer key, so only referenceless checks run here at all (the test from 0.2).
- **The loop is the point: online discovers, offline prevents recurrence.** A finding that stops at the dashboard helps once. Carried into a gated offline test, it protects every release after.

## 4.2 Sampling and alerting

- **Sample judged checks; never sample deterministic ones.** Judges cost per call. Deterministic checks are free — run them on everything.
- **Pick the sample rate from the change you must detect**, not from a round number that felt affordable. A small sample can only resolve a large change: sampling 5% of 2,000 daily traces pins a score to roughly ±4.5 points, so a 2-point drop is invisible in it.
- **An alert set tighter than that resolution fires on noise**, gets muted within a month, and leaves you with monitoring that looks healthy and tells nobody anything.
- **Your first alert shouldn't be a quality metric.** Trace volume, error-span rate, scorer coverage — those catch the case where monitoring itself silently stopped.

## 4.3 What tracing adds that hand-built examples can't

- **Tracing** — the production version of a hand-rolled trace list, captured by instrumentation.
- **Router and tool evaluations** — the same questions as 2.2, computed from real spans.
- **Path-efficiency experiments** — the same question as checks 4 and 9 in 3.1, but run through a reusable dataset-plus-evaluator setup that generalizes to any agent, instead of a one-off script over one hand-built trace.

## 4.4 Two ideas that are genuinely new

- **Skill evaluation** — judging a *tool's own output quality* in isolation. Is the generated SQL correct? Does the chart code run? A well-chosen tool that does its job badly is invisible to every check in Parts 2 and 3: selection passes, arguments pass, output is quietly wrong.
- **Version comparison** — re-running the same experiment against a system with one deliberate change. Everything earlier judges one run in isolation. This is the answer to "did my prompt change actually help, or did it just feel better?"

---

# Part 5 — Real Multi-Agent Systems

Applying all of the above to a running multi-agent system surfaces what hand-built examples can't teach.

- **A multi-agent system is a different shape.** Several narrow agents hand work to each other; one's output is the next one's input. You're evaluating the *combined* output of a handoff chain.
- **Handoffs are where quality dies, and they need their own measurement.** The same multiplication as 2.1: five components each right 90% of the time are all right together only 0.9⁵ ≈ 59% of the time — before counting routing errors and context lost at each boundary. **That's how every subagent scores above 0.9 while end-to-end scores 0.6**, and why per-agent numbers will never explain it.
- **Attribution requires nested traces.** Session → orchestrator turn → subagent invocation → spans. Without nesting you know quality dropped; with it you know *which subagent*, on *which turn*.
- **Score routing separately from the parts.** Handoff accuracy is usually the first thing to break when a subagent is added — the rubric was written for N agents and now runs against N+1.
- **Write the task description explicitly.** "A trip plan" might really mean top-3 interest matches, 5 attractions, a day-by-day itinerary, and budget guidance.
- **Mind the gap between "an eval script exists" and "it sees what it needs."** A batch script calling a public API often has only the final output, not the internal calls. An approximated list beats none — but name the gap instead of papering over it.
- **Every measurement has a scope of validity, and it expires silently.** A check correct for a one-tool agent misleads the moment a second tool arrives. Nothing errors. The number just stops meaning what it meant.

---

# Quick Reference

## The evaluation debugging loop

When someone says "the answers got worse," work the layers in order rather than guessing:

1. **Reproduce it as a measurable claim.** "Worse" is not a metric. Get 20 specific flagged conversations.
2. **Diff everything that changed** — model version, prompt, tool schemas, retrieval index, truncation behaviour, temperature.
3. **Check retrieval first.** Did the right chunk come back at all? If the evidence never arrived, nothing downstream matters.
4. **Check grounding.** Right chunk retrieved, answer ignores it — a different bug with a different fix.
5. **Check the tool spans.** Soft failures (2.4) live here and show up nowhere else.
6. **Check the metric nobody was watching.** The classic: the requested metric rose and three others collapsed.
7. **Check whether the benchmark is what's wrong.** A benchmark improving while users complain means its distribution doesn't match traffic.
8. **Slice everything.** Aggregates hide the thing you need to see.

## Question → measurement

| If you're asking... | Reach for |
| --- | --- |
| Retrieval quality, with labels | Precision@K, Recall@K, MRR, nDCG (1.1) |
| Retrieval quality, without labels | Judged contextual precision / recall / relevancy (1.2) |
| Is the answer grounded, no reference available? | Answer relevancy, faithfulness, trusted-context check (1.3) |
| Is the answer *correct*? | A custom correctness rubric; similarity as a proxy (1.4) |
| Should the check run inside the pipeline? | In-pipeline relevance and grounding you can branch on (1.6) |
| From one example to a verdict on the system? | The batch pattern (1.7) |
| Full pipeline, many queries | Golden dataset + full suite, sliced (1.8, 1.9) |
| Does the conversation hold up? | Per-turn relevance, retention, whole-dialogue rubric — and the session-level number, not just the turn-level one (2.1) |
| Right tools, right arguments? | Selection comparison, schema validation, judged check (2.2) |
| Did it get the job done? | Judged completion, custom rubric, or end-state verification (2.3) |
| Did a tool fail quietly? | Deterministic check reading the tool output (2.4) |
| Was the *path* efficient? | The nine trajectory checks (3.1) |
| How would I measure this on a live system? | Spans from tracing; the trace store as a queryable table (3.3) |
| Which checks can run in production? | Any that doesn't need an answer key written in advance (0.2) |
| Did my change help? | Version comparison — same dataset, one deliberate change (4.4) |
| Why is end-to-end worse than every component? | Composition across handoffs; nested traces to attribute it (Part 5) |

## One-page cheat sheet

- Name the layer before naming a metric.
- Ask whether the check needs an answer key written in advance — that decides offline vs online.
- Climb the cost ladder from the bottom; stop at the rung that answers the question.
- Deterministic where you can, judged where you must, and never gate on a judge you haven't checked against humans.
- Measure judge agreement, not judge average.
- Mechanics ≠ process ≠ outcome. Score all three.
- Read the tool span, not just the final string.
- Score the absence of a call as an outcome.
- Fail unexpected tools as well as missing ones.
- Combine sub-scores with minimum, not mean.
- Report session-level numbers beside turn-level ones.
- Distinguish "not measured" from "failed", always.
- Verify the system of record wherever a real side effect exists.
- Slice before you conclude.

## The five that matter most

1. **Taxonomy first.** Know whether you're diagnosing retrieval, generation, mechanics, trajectory, or outcome before picking anything.
2. **Reference-based vs referenceless is a cost decision.** The mechanical test — *does it need an answer key written in advance?* — tells you which is which, and which can go online.
3. **LLM-as-judge is a tool with known failure modes, not an oracle.** Unvalidated, it measures change, not quality.
4. **Mechanics ≠ process ≠ outcome.** Right tool and right arguments doesn't mean a sound sequence; a sound sequence doesn't mean the goal was met.
5. **The strongest signal is the real system of record.** End-state verification beats every judged measurement — it cannot be fooled by a confident sentence.

**And cutting across all five:** aggregates hide the thing you need to see.
