# Agents: Tools, Conversations, Trajectories, Outcomes

*Score mechanics, process and outcome separately, because passing any one of the three says
nothing about the other two.*

◷ 23 min · Level 2 · [Level 0](00-orientation-v2.md) named tool mechanics, trajectory and outcome
as three of the five evaluable layers. This is where each gets built out, plus the multi-turn
axis Level 0 flagged and left open.

A good final reply is not evidence the agent did the job. The sentence *"Your flight is booked!"* reads identically whether the booking call succeeded,
failed, or never happened. This level pulls apart three questions that a single quality score
fuses into one.

> **Who this is for.** No library knowledge is assumed. Every technical term is defined in plain
> words the first time it appears.

---

Picture a customer-support agent with three tools: `search_orders`, `get_refund_policy`, and
`issue_refund`. A user writes: *"My order #4521 arrived broken, can I get a refund?"* A single "was the final
reply good?" check cannot say much here. Five different things can go wrong on the way, and
each needs a different fix. The wrong tool, or the right tool with a typo'd order
ID. Every tool called correctly and a refund $30 over the user's stated budget. Five steps for a
three-step job. A fluent *"Your refund of $45 has been issued"* with no refund recorded
anywhere. Or every turn handled well and the conversation still ending somewhere it shouldn't.

**Mechanics ≠ process ≠ outcome.** Whether the calls were mechanically correct, whether the path
was sound, and whether the real-world result happened are three separate questions. Everything
below runs on that one refund-agent example.

```mermaid
flowchart LR
    A["Mechanics<br/>right tool, right arguments?"] -.->|"doesn't guarantee"| B["Process<br/>sound path, no waste,<br/>recovered from errors?"]
    B -.->|"doesn't guarantee"| C["Outcome<br/>did the real side effect<br/>actually happen?"]
    style A fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
    style B fill:#EDE3CE,stroke:#9A6A12,color:#0E2226
    style C fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

---

## 1. Score the Conversation, Not Just the Turn

Every check in Levels 0 and 1 scored one request/response pair. Real chatbots hold a conversation. Earlier turns constrain what a later turn should say. A
system can pass every individual turn and still fail the conversation.

### Why "95% per turn" is not 95% conversation quality

This is the most important arithmetic in the level, and almost nobody does it by default. If
each turn independently passes at rate *p*, the chance that **all** *n* turns pass is *p* raised
to the power *n*. Every turn has to go right, not most of them.

| Turn pass rate | 3 turns | 5 turns | 10 turns |
| --- | --- | --- | --- |
| 0.99 | 0.970 | 0.951 | 0.904 |
| **0.95** | 0.857 | **0.774** | 0.599 |
| 0.90 | 0.729 | 0.590 | 0.349 |

At a healthy-looking **95% per turn**, a conversation is more likely failed than not by **turn
14**. That is the *optimistic* version. It assumes turns fail independently, when in practice
one bad turn poisons the context for every turn after it, so real rates land below the table.

**Report the session-level number beside the turn-level one.** A dashboard showing "95% turn
quality" and a customer saying "conversations fall apart" describe the same system. The
dashboard is reporting it in the wrong unit. It follows that multi-turn systems need a
conversation-level gate, not only a turn-level one — see
[Level 6](06-the-release-gate-and-ci-v2.md).

### The three things worth checking across turns

A whole dialogue is represented as an ordered list of turns and scored three ways:

| Check | What it asks |
| --- | --- |
| **Turn relevancy** | Over a sliding window of recent turns, is the last assistant turn relevant to what came before it? |
| **Knowledge retention** | Does the assistant correctly remember and reuse information the user supplied earlier? |
| **A custom conversational rubric** | Your own standard applied across the whole dialogue — "never diagnose, always recommend a doctor for serious concerns" for a medical chatbot |

Hand-writing dialogues does not scale. Simulating them does. Prompt a model to role-play "an
angry customer" or "someone who keeps changing their mind". Give it a goal and a policy, and
let it produce dialogues, curveballs included.

### Failures with no single-turn representation

Some failures cannot show up in any single-turn check. What makes them wrong happened in a
*different* turn from where the problem is visible.

**Acting without consent** is the sharpest case. *"I've opened a ticket for you"* on turn one,
unasked. Read alone, that reply is helpful, on-topic, grounded, and reports a completed action —
every single-turn check passes it. **The agreement that should have come first lives between turns, so there is nowhere for its
absence to show up.** Most write actions are gated by a prompt instruction rather than by the
tool refusing, so that obedience has to be tested. Two relatives behave the same way. Ignoring
a refusal: the user says "no, don't do that" on turn two, and it happens on turn four. Drift:
every turn is fine, and the conversation still ends somewhere it shouldn't.

**Score three outcomes here, not two** — *complied*, *violated*, and *stalled*, where the
customer agreed and then nothing happened. Stalled is not dangerous the way violated is, but the
customer asked for something and did not get it, and it needs a different fix than either.

One consequence is worth stating precisely. **A conversation-level check run on a single-turn
interaction must report "not measured", never zero.** An unmeasured check and a failed one must
never look identical on a dashboard.

```mermaid
flowchart TD
    Q{"Did the customer ask<br/>for this action?"}
    Q -->|"Yes, and it happened"| OK["Complied"]
    Q -->|"Yes, but nothing happened"| STALL["Stalled — not dangerous,<br/>but unmet. Different fix."]
    Q -->|"No"| VIOL["Violated — the business risk.<br/>No single-turn check sees it."]
    style OK fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
    style STALL fill:#EDE3CE,stroke:#9A6A12,color:#0E2226
    style VIOL fill:#F2D9D9,stroke:#9A3B3B,color:#0E2226
```

---

## 2. Check the Mechanics: Right Tool, Right Arguments

Tool use is where an agent's output stops being text. It becomes a decision. A travel bot that says *"Your flight is booked!"* is useless if it never called the booking
API. **The confident sentence looks identical whether the call succeeded, failed, or never
happened.**

| | Standard LLM evaluation | Tool-using agent evaluation |
| --- | --- | --- |
| **What you score** | One output against a reference | A sequence of decisions, *then* the output |
| **Where failure lives** | In the text | Underneath it — which tool, what order, what arguments, how results were read |
| **What a good-looking reply proves** | Usually that it's good | Nothing on its own — it could be describing a tool call that never happened |

Three checks answer different questions at different granularities:

| Check | Type | Needs | Best for |
| --- | --- | --- | --- |
| **Tool selection** | Reference-based, deterministic | The expected tool list | Regression and CI, where correct behaviour is already known |
| **Argument correctness** | Referenceless, judged | Tool descriptions only | Dynamic workflows and production, where correct argument values can't be pre-written |
| **Multi-turn tool use** | Multi-turn, judged | The list of available tools | Conversational agents, where tool use spans exchanges |

### Strict vs. loose matching: the same check can score 1.00 or 0.00

**Strictness lives in how the check is configured, not in the agent's behaviour.** The usual
default is looser than it looks. Take one expected trajectory: a flight search NYC→London on
2026-03-13, then a weather check for London that date. Run it against six traces — an exact
match, an extra unrequested currency conversion, the two calls in the wrong order, a missing
flight-search output, a transposed date (`03-31` for `03-13`), and a missing weather check.
Five of the six are broken in a way that should matter.

| Configuration | What it actually compares | Mean score across the six traces | What it misses |
| --- | --- | --- | --- |
| **A · names only** (the usual default) | Is a tool with this *name* present anywhere in the list? | **0.92** | Order, arguments, outputs and extra calls are all invisible — 5 of 6 traces score 1.00, and 4 of those 5 are broken |
| **B · names + arguments** | Names *and* arguments must match, still order-blind | 0.83 | Catches the wrong date (drops to 0.50). Still misses the extra call, the reversed order, and the dropped output |
| **C · exact list equality** | Same tools, same arguments, same recorded outputs, same order | 0.17 (5 of 6 score exactly 0) | Catches all five broken traces — and turns the check binary |

**Config A reading 0.92 is not measuring tool correctness. It is measuring whether the agent knows the tools exist.** A dashboard built on that default
looks nearly perfect. It is missing a reversed sequence, a silently dropped output and a wrong
travel date, all at once.

Both extremes are wrong in their own way, which is why strictness is a decision rather than a
setting left alone. Too strict — exact tools, exact order, nothing extra — and an agent that
harmlessly also checked the weather fails the whole run. Too loose — expected tools appear
somewhere, extras ignored — and an agent firing all eight of its tools on every question passes
every time. It is spraying, and the check applauds.

**Demand strict ordering only where the order genuinely is the requirement.** A flight cannot
be booked before it is searched for, so that ordering is real. Whether the weather check came
first or third usually is not.

A selection check can also be handed the list of tools the agent *could* have called. Without
it, the check compares called tools to expected tools mechanically. With it, a judge also asks
whether the agent picked the *best* available tool.

> **Turning that on escalates a pure code check into a partly-judged one** — Level 0's cost
> ladder, applied to a single metric.

### Argument correctness: cheap check first, judge second

"Were the arguments right?" is two questions, and they do not cost the same. **Is it even
well-formed?** Does the booking call have a date field, and is `2026-02-31` a real date? Plain
code answers that — free, instant, never wobbles. **Does it make sense for what was asked?** The
user wanted a morning flight to Delhi; did it book an evening flight to Dubai? Only a judge
answers that.

The pattern is to validate the schema deterministically first, and spend the judge call only if
that passes.

```python
# A structurally malformed call is worth zero -- no point spending a judge call
# to have a model tell you the date field isn't a date.
valid, reason = validate_args(test_case.tools_called)
if not valid:
    print(f"Score: 0\nReason: {reason}")   # judge never runs -- free rejection
else:
    metric.measure(test_case)              # now spend the LLM call
```

### Combine sub-scores with the worst one, not the average

Where a check has a selection score and an argument score, the final score should be the
**minimum** of the two. Suppose selection scores 1.0 — exactly the right tool — and arguments
score 0.0, because it handed that tool nonsense. The mean says 0.5, which reads as "half
working". **Nothing was half working: the booking failed.** The minimum says 0.0, which is the
truth. Averaging lets a healthy dimension cover for a broken one, which is the exact failure the
check exists to catch.

### Doing nothing is behaviour, and it needs scoring too

"What's your refund policy?" should produce **no tool call at all**. The agent should answer from
what it knows and stop. That restraint is correct and deserves a passing score, not silence.

Most suites only inspect the calls that happened, which leaves them blind in both directions.
**Should have stayed still, and moved.** It calls a tool it did not need, wasting money and
adding one more thing that can go wrong. That stays invisible, because the calls that did
happen were correct. **Should have moved, and stayed still.** It says *"your flight is
booked!"* without ever calling the booking tool. Also invisible, because there is no call to
inspect.

So the expected-tool list has to be allowed to be an **empty set**, and an empty set has to be
something a run can pass or fail against, exactly like any other expected value.

---

## 3. Verify the Outcome, Not the Sentence

Everything in Section 2 judges mechanics. None of it asks the question the user cares about: did
the agent get the job done?

The gap is real in both directions. An agent can call every tool correctly and still book the
wrong hotel, because it silently dropped a stated budget. A slightly inefficient sequence can
still land on a fine outcome. A production suite needs both.

### Task completion as a judged check

A task-completion check is judged and referenceless. It reads the user's goal, the final
answer, and the list of tools called. Then it asks whether the underlying task was
accomplished. Passing the tool list is optional in most toolkits and worth doing anyway.

The case worth holding onto: an agent books a real, valid hotel reservation through
correctly-formed calls, but the price is $30/night over the user's stated $150 budget. Selection
and argument checks both score that run well, because the tools were right and the arguments
well-formed. A task-completion check is built to catch that the actual requirement — staying
under budget — was not met.

It is what lets the judge see *how* the outcome was reached, not only what the agent claims. Where the real task is broader than the literal wording, state it explicitly rather than
letting the check infer it from the last message. A constraint mentioned earlier in a
conversation is exactly the case that gets lost. A full execution trace also beats a flat list
of calls, because a trace carries the agent's intermediate reasoning.

### Two escalations beyond a generic check

A generic check uses a fixed definition of "done". Two situations call for going further.

**When "done" is domain-specific**, write a `GEval` rubric instead of the generic prompt — *"the
summary must cite at least two sources"*, *"a refund response must never promise a dollar amount
before policy lookup"*. It costs more to author, and applies a local bar rather than a general one.

**When the stakes are too high for a judge at all**, verify the side effect. A generic check and
a custom rubric are both still a model reading text. After a "book the hotel" task, query the
booking system for a confirmed reservation matching the dates and budget.

> **A state-based check cannot be fooled by a fluent-but-wrong response.**

In practice, combine them. Use a deterministic state check as the pass/fail gate wherever a
checkable outcome exists. Keep a judged check as a secondary signal for the genuinely fuzzy
parts, like tone or the completeness of an explanation.

### Reading the record beats every judged check

*"Your refund of $45 has been issued"* reads as confident and complete whether or not a refund
happened. The order database, the booking system and the ledger cannot be fooled that way,
because they hold the event rather than a *description* of it.

> **Wherever a real side effect exists to check, reading it is the strongest signal in this
> level** — and it is free and deterministic.

One failure hides underneath all of this. A tool can fail softly instead of raising — `found:
false`, an empty result, a 200 with an empty payload. The model gets something that *looks*
like data. It fills the gap with a plan and a balance for an account that does not exist.
Nothing crashes. Nothing alerts.

> **Neither grounding nor task success reads the tool's own output**, which is the only place
> this failure is visible.

The fix is a deterministic check that reads the tool result and, on failure, asserts the response
does not state the facts that tool was meant to supply. Pair it with making "I couldn't retrieve
that" an explicitly rewarded behaviour, because prompting alone does not fix it.

---

## 4. Judge the Path, Not Only Where It Ended

Given a multi-step run, was the *path* any good, independent of where it ended up? An agent can
reach the right answer in twice the steps. It can retry blindly instead of correcting. It can
repeat an identical call for no new information.

> **Sections 2 and 3 see none of that.** They read the final list of calls and the final answer,
> never the shape of the trace that produced them.

The standard approach runs the agent's loop to build a **trace**: a step-by-step record of what
was called, with what arguments, and what happened. That trace then goes to a *separate*
evaluation pass, scored against a **gold trajectory** — the sequence a human decided ahead of
time was correct. The agent never grades itself.

### The refund-agent scenario, and the nine checks against it

One deliberately messy trace exercises all nine checks at once: the support agent working the
order-#4521 refund. Its five-step trace contains a typo'd order ID that fails, a corrected retry that succeeds, a
policy lookup, an identical *redundant* repeat of that lookup, and finally the refund. The
refund really does mutate a mock order database, so end-state verification has something real
to check.

| # | Check | What it catches | Level in this trace |
| - | --- | --- | --- |
| 1 | **Tool selection accuracy** | Coverage only — does the called set include every tool in the gold set? Loosest of the nine | Outcome |
| 2 | **Argument correctness** | Right tool, invalid or malformed arguments | Outcome |
| 3 | **Redundant calls** | A (tool, arguments) pair that already *succeeded* earlier in the same trace | Step |
| 4 | **Step-wise accuracy** | Fraction of steps that made real forward progress (succeeded *and* weren't redundant) | Step |
| 5 | **Task success rate** | The ground-truth outcome for this one run | Outcome |
| 6 | **Trajectory match (fuzzy)** | Successful tool *set* vs. gold set, ignoring order and retries | Outcome |
| 7 | **End-state verification** | Reads the mutated system of record directly — not the agent's own claimed answer | Outcome |
| 8 | **Recovery / self-correction rate** | After an error, did a *later* step call the same tool and succeed? | Step |
| 9 | **Cost / efficiency proxy** | Redundant calls and errors treated as waste; `1 - wasted/total` | Step |

### Five of these nine never move

This is the most important reading of the scenario, and the reason step-level and outcome-level
checks have to run together. Progressively cleaning the same trace shows which checks are
sensitive to waste and which are not:

| Trace variant | Steps | Redundant (#3) | Step-wise (#4) | Recovery (#8) | Cost/efficiency (#9) |
| --- | --- | --- | --- | --- | --- |
| As actually traced | 5 | 1 | 0.60 | 1.00 | 0.60 |
| Without the redundant call | 4 | 0 | 0.75 | 1.00 | 0.75 |
| Without the typo'd ID (nothing to recover from) | 4 | 1 | 0.75 | n/a | 0.75 |
| Minimal clean path | 3 | 0 | **1.00** | n/a | **1.00** |

Checks **1, 2, 5, 6 and 7** stay flat and passing across all four variants. The agent used every
tool it needed and the refund really was recorded, waste or no waste. **Step-wise accuracy and
cost/efficiency swing from 0.60 to 1.00** as the waste comes out.

> **Task success alone reports "pass" on the messiest version of the trace** and says nothing
> about the wasted policy lookup or the wrong order ID that cost 40% more calls than needed.

The two checks that cannot be fooled by a fluent sentence are worth seeing as code, because they
are Section 3's "read the record, not the string" principle in practice:

```python
# 7 -- End-State Verification. Do NOT read result["final_answer"]; the agent
# wrote that string and it can be wrong. Read the system of record instead.
def end_state_verified(order_db_after, order_id, expected_amount):
    order = order_db_after[order_id]
    return order["refund_issued"] is True and order["refund_amount"] == expected_amount

# 8 -- Recovery. For every errored step, did a LATER step call the same tool
# and succeed? That is the difference between self-correction and blind retry.
def recovery_rate(trace):
    errors = [(i, s) for i, s in enumerate(trace) if s["status"] == "error"]
    if not errors:
        return None   # None, not 1.0 -- there was nothing to recover from
    recovered = sum(
        1 for i, s in errors
        if any(l["tool"] == s["tool"] and l["status"] == "ok" for l in trace[i + 1:])
    )
    return recovered / len(errors)
```

Recovery returns `None`, never `1.0`, when there were no errors. That is Section 1's "unmeasured
must never look like passed" rule again.

### Three traps

**The tool-selection scorer that scores 100% for calling everything.** The common version
computes both missing and unexpected tools but bases the verdict only on the missing ones. Fail
both directions — an unexpected account lookup on an unrelated request is a privacy problem, and
a coverage-only check never sees it.

**Exact-sequence matching as the default.** It fails on a mid-trace typo or a harmless extra
lookup. Use fuzzy matching — the *successful* tool set against the gold set, order and retries
ignored — and demand exact ordering only where order genuinely is the requirement.

**Rewarding recovery on its own.** A high recovery rate is good news. Pair it with step-wise
accuracy, or the reward goes to a system that generates errors to have something to recover from.

### From a hand-built trace to a live system

Hand-computing all nine from a toy trace is how the checks get learned. On a running system the
*questions* do not change. Only the source of each answer does:

| Question | Where the answer comes from in production |
| --- | --- |
| Did it call the tools it needed? | Gold tool set stored beside the eval questions; called set read from the tool spans tracing already captures |
| Were the arguments valid? | Typed tool signatures reject a malformed call before it executes — the failure never reaches evaluation |
| Did it repeat itself? | Query the trace store for duplicate (tool, arguments) spans inside one request — pure SQL, no judge |
| Did each step make progress? | A per-step scorer walking each trace's spans, run as part of the eval job |
| Did the task succeed? | An eval set of (task, expected outcome) pairs, run on a schedule, trended over time |
| Was the path close to gold? | Gold trajectories stored as structured data; a comparison function registered once |
| Did the real effect happen? | A before/after diff of the system-of-record table, taken in the same run as the agent |
| Did it recover? | Tracing marks error spans automatically; a job matches them against later successful spans in the same trace tree |
| What did it cost? | Tracing captures tokens and latency per span automatically — query the trace table |

**Instrumentation is the precondition under every row of that table, not an implementation
detail. An untraceable agent is unevaluable.** Every request needs a span per retrieval, per
model call and per tool call, carrying tokens and latency, or none of these nine checks have
anything to read.

---

## 5. Rehearse the Design-Round Follow-Ups

Four questions test this level directly. Each is a decomposition problem in a dashboard's
clothing.

**"Per-turn quality is 95%, but the customer says conversations fall apart. Can both be true?"**

Both are true, and it is arithmetic rather than a mismatch. A weak answer assumes the complaint
must be about one hard category and proposes slicing by topic. Section 1's table shows a uniform
95% failing about a quarter of five-turn conversations. Track *where* conversations first break,
not just the rate.

**"What kind of failure can only be seen across turns?"**

Acting without consent. A weak answer says "multi-turn failures are mostly about memory, so I'd
add a context-retention check" — naming the most benign member of the family and stopping. The
final reply can pass every single-turn check and still be wrong, because the missing agreement
lived in an earlier turn. Score complied / violated / stalled, not pass / fail.

**"How do you evaluate whether an agent took an efficient path, not just a correct one?"**

Assert *properties* of the path — recovery, redundancy, ordering — rather than prescribing one
gold sequence. A weak answer defines the expected tool sequence per test case and scores how closely the
actual sequence matches. That encodes one path when several are valid. It then becomes a
maintenance burden, and gets loosened until it measures nothing.

**"The agent has five tools. What new evaluation risks does that create?"**

The real risk is a check silently changing meaning, not coverage. A weak answer treats it as
"more combinations to test". A check like "was a tool called when one was expected?" is correct
for a one-tool agent and **passes a wrong-tool call once there are five**. Nothing turns red, and
the check is now certifying the failure. Scorers have a scope of validity a system can outgrow,
so audit them whenever the agent gains a capability.

That last risk is worth carrying forward on its own. **Wrong-tool is worse than no-tool**,
because it returns data that is genuine, irrelevant and confidently presented — far more
convincing to a user, and to a judge, than a missing answer.

---

## Key Takeaways

- Per-turn quality compounds: 95% a turn is 77% over five turns, so report the session-level
  number beside the turn-level one.
- Acting without consent has no single-turn representation, and the three outcomes to score are
  complied, violated and stalled — never pass/fail.
- Tool-matching strictness is a decision, not a default; names-only matching scores 0.92 on six
  traces of which five are broken.
- Combine a selection score and an argument score with the minimum, because averaging lets a
  healthy dimension cover for a broken one.
- An empty expected-tool set is a real expectation: restraint deserves a passing score, and a
  claimed action with no call deserves a failing one.
- Wherever a real side effect exists, reading the system of record beats every judged check, and
  it is free.
- Five of the nine trajectory checks never move as waste is removed, so step-level and
  outcome-level checks have to run together.
- An untraceable agent is unevaluable — instrumentation is the precondition, not a detail.

## Check Yourself

1. Turn-level quality is 95% and a customer says five-turn conversations fall apart. Who is
   wrong? **Neither. 0.95 to the fifth power is 0.774, so roughly a quarter of five-turn
   conversations fail. The dashboard is reporting in the wrong unit.**
2. An agent replies "I've opened a ticket for you" on turn one, unprompted. Which single-turn
   check catches it? **None. The reply is helpful, on-topic and grounded. The missing agreement
   lives between turns, so there is nowhere for its absence to show up.**
3. A conversation-level check runs against a single-turn interaction. What must it report?
   **"Not measured" — never zero. An unmeasured check and a failed one must never look identical
   on a dashboard.**
4. Tool selection scores 1.0 and argument correctness scores 0.0. What is the combined score, and
   why? **0.0, the minimum. The booking failed; a mean of 0.5 would read as "half working" when
   nothing was.**
5. A suite only inspects calls that happened. Name the two failures it cannot see. **A tool
   called that wasn't needed, and a claimed action with no call behind it. Both need the expected
   set to be allowed to be empty.**
6. A tool returns `found: false` and the agent answers with a balance anyway. Which checks miss
   it? **Grounding and task success both — neither reads the tool's own output. Only a
   deterministic check on the tool result sees it.**
7. Cleaning the waste out of a trace moves two of the nine checks and leaves five flat. What does
   that tell you about task success? **It reports "pass" on the messiest trace. Outcome checks
   cannot see waste, so step-level checks have to run alongside them.**
8. A one-tool agent's "was a tool called when expected?" check gains four more tools. What
   happens? **It starts passing wrong-tool calls. The check's scope of validity was outgrown, and
   nothing turns red to say so.**

---

## References

All content above was drawn only from material already in this repository. Nothing here was
invented, and no external source was consulted. This page is a restyled edition of
`02-agents-tools-conversations-trajectories-outcomes.md`; its content is the same, with library
class names replaced by what each check does.

**Notebook:**

- `courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb` — the
  turn-list representation of a dialogue, the three multi-turn checks, and conversation
  simulation.
- `courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb` — tool selection, argument
  correctness, multi-turn tool use, the two-pass argument-validation pattern, and the
  minimum-not-average design.
- `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb` — task completion,
  the budget-violation worked example, the custom-rubric escalation, and the case for state-based
  outcome verification.
- `courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb` — the nine
  trajectory checks, the refund scenario, and the `end_state_verified` / `recovery_rate`
  functions.

**Docs:**

- `docs/concepts/rag-agent-tool-evaluation.md`, Part 2 (§2.1–2.4) and Part 3 (§3.1–3.3) — the
  multi-turn arithmetic and consent/stalled framing, the tool-use properties, the
  task-completion escalation ladder, the "polite tool failure" mode, the nine trajectory checks,
  the three traps, and the hand-built-trace-to-live-system table.
- `docs/concepts/databricks-mlflow-evals.md`, Part 4 — the conversation-success table used in
  Section 1.
- `docs/interactive-labs/04-tool-use-evaluation.html` — the six-trace, three-configuration
  strictness comparison used in Section 2 (its 0.92 / 0.83 / 0.17 mean scores were independently
  recomputed against the page's own scoring logic before use here).
- `docs/interactive-labs/05-agent-trajectory-evaluation.html` — the four-variant table used in
  Section 4, and the observation that five of the nine checks never move across those variants.
- `docs/interview-prep/QUESTION_BANK.md`, Part 7 (Q26–Q29) — the four questions reproduced in
  full in Section 5 rather than pointed at.
- `docs/study-guide/evaluation-roadmap.md` — Level 2's topic list and goal statement.
- `docs/study-guide/evaluation-topic-notebook-mapping.md` — Level 2's resource table.
- `labs/multiturn-and-tool-eval/README.md` — checked and found to introduce no topic beyond what
  course 01 already covers.

**Limitations.** This file was written by reading the repository's own material, not by running
any notebook or calling any API — no cost was incurred producing it, consistent with this
project's rule against executing anything that spends money without being asked. The percentage
figures in Section 2's strictness table and Section 4's trajectory-variant table were recomputed
by hand against the scoring logic in each interactive lab's own source, not copied from a live
run. This file does not independently verify any vendor's documentation.
