# Agents: Tools, Conversations, Trajectories, Outcomes

*Score mechanics, process and outcome separately, because passing any one of the three says nothing about the other two.*

◷ 20 min read · Level 2 · [Level 0](00-orientation.md) named tool mechanics, trajectory and outcome as three of the five evaluable layers. This is where
each gets built out, plus the multi-turn axis Level 0 flagged and left open.

A good final reply does not prove the agent did the job. The sentence *"Your flight is booked!"* reads the same whether the booking call succeeded,
failed, or never happened. A single quality score fuses three questions into one. This level pulls them apart.

> **Who this is for.** No library knowledge is assumed. Every technical term is defined in plain words the first time it appears.

---

Picture a customer-support agent with three tools: `search_orders`, `get_refund_policy` and `issue_refund`. A user writes: *"My order #4521 arrived
broken, can I get a refund?"* One "was the final reply good?" check cannot say much here. Five different things can go wrong on the way, and each
needs a different fix:

- **Wrong call.** The wrong tool, or the right tool with a typo'd order ID.
- **Missed constraint.** Every tool called correctly, and a refund $30 over the user's stated budget.
- **Wasted steps.** Five steps for a three-step job.
- **No real effect.** A fluent *"Your refund of $45 has been issued"* with no refund recorded anywhere.
- **Conversation drift.** Every turn handled well, and the conversation still ends somewhere it shouldn't.

**Mechanics ≠ process ≠ outcome.** Correct calls, a sound path and a real-world result are three separate questions. Everything below runs on that one
refund-agent example.

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

Every check in Levels 0 and 1 scored one request/response pair. Real chatbots hold a conversation. Earlier turns constrain what a later turn should
say. A system can pass every turn and still fail the conversation.

### Why "95% per turn" is not 95% conversation quality

Say each turn passes on its own at rate *p*. The chance that **all** *n* turns pass is *p* raised to the power *n*. Every turn has to go right.

| Turn pass rate | 3 turns | 5 turns | 10 turns |
| --- | --- | --- | --- |
| 0.99 | 0.970 | 0.951 | 0.904 |
| **0.95** | 0.857 | **0.774** | 0.599 |
| 0.90 | 0.729 | 0.590 | 0.349 |

At a healthy-looking **95% per turn**, a conversation is more likely failed than not by **turn 14**. That is the *optimistic* version:

- **The table assumes independence.** It treats each turn as failing on its own.
- **Real failures spread.** One bad turn poisons the context for every turn after it. Real rates land below the table.

**Report the session-level number beside the turn-level one.** A dashboard showing "95% turn quality" and a customer saying "conversations fall apart"
describe the same system. The dashboard reports it in the wrong unit. Multi-turn systems need a conversation-level gate as well as a turn-level one
(see [Level 6](06-the-release-gate-and-ci.md)).

### The three things worth checking across turns

A whole dialogue is stored as an ordered list of turns and scored three ways:

| Check | What it asks |
| --- | --- |
| **Turn relevancy** | Over a sliding window of recent turns, is the last assistant turn relevant to what came before it? |
| **Knowledge retention** | Does the assistant correctly remember and reuse information the user supplied earlier? |
| **A custom conversational rubric** | Your own standard applied across the whole dialogue, such as "never diagnose, always recommend a doctor for serious concerns" for a medical chatbot |

Hand-writing dialogues does not scale. Simulating them does. Prompt a model to role-play "an angry customer" or "someone who keeps changing their
mind". Give it a goal and a policy. Let it write the dialogues, curveballs included.

### Failures with no single-turn representation

Some failures cannot show up in any single-turn check. What makes them wrong happened in a *different* turn from the one where the problem shows.

**Acting without consent** is the clearest example. The agent says *"I've opened a ticket for you"* on turn one, unasked. Read alone, that reply
looks fine:

- **Every single-turn check passes it.** It is helpful, on-topic and grounded, and it reports a completed action.
- **Where it fails.** **The agreement that should have come first sits between turns. Its absence has nowhere to show up.**

Most write actions are gated by a prompt instruction rather than by the tool refusing. That obedience has to be tested. Two relatives behave the same
way:

- **Ignoring a refusal.** The user says "no, don't do that" on turn two, and it happens on turn four.
- **Drift.** Every turn is fine, and the conversation still ends somewhere it shouldn't.

**Score three outcomes here, not two:**

- **Complied.** The customer asked for the action, and it happened.
- **Violated.** The agent acted without being asked.
- **Stalled.** The customer agreed, and then nothing happened. Stalled is not dangerous the way violated is. The customer still asked for something
  and did not get it, and it needs a different fix than either.

**A conversation-level check run on a single-turn interaction must report "not measured", never zero.** An unmeasured check and a failed one must
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

Tool use is where an agent's output stops being text and becomes a decision. A travel bot that says *"Your flight is booked!"* is useless if it never
called the booking API.

The thing being scored is a sequence of decisions, then the output. Three checks cover it at three levels of detail:

- **Tool selection.** Reference-based (compared against an expected list), for CI.
- **Argument correctness.** Referenceless and judged, for production.
- **Multi-turn tool use.** Tool calls across a whole dialogue.

The field guide's [tool use section](../concepts/field-guide/05-conversations-tools-and-task-completion.md#2-tool-use) defines each one and compares
tool-use evaluation with ordinary output scoring. This section covers what the definitions leave out: how much the configuration changes the number.

### Strict vs. loose matching: the same check can score 1.00 or 0.00

**Strictness is set in how the check is configured.** The default is looser than it looks. Take one expected trajectory: a flight search from NYC to
London on 2026-03-13, then a weather check for London that date. Run it against six traces:

- an exact match
- an extra, unrequested currency conversion
- the two calls in the wrong order
- a missing flight-search output
- a transposed date (`03-31` for `03-13`)
- a missing weather check

Five of the six are broken in a way that should matter.

| Configuration | What it actually compares | Mean score across the six traces | What it misses |
| --- | --- | --- | --- |
| **A · names only** (the default) | Is a tool with this *name* present anywhere in the list? | **0.92** | Order, arguments, outputs and extra calls are all invisible. 5 of 6 traces score 1.00, and 4 of those 5 are broken |
| **B · names + arguments** | Names *and* arguments must match, still order-blind | 0.83 | Catches the wrong date (drops to 0.50). Still misses the extra call, the reversed order, and the dropped output |
| **C · exact list equality** | Same tools, same arguments, same recorded outputs, same order | 0.17 (5 of 6 score exactly 0) | Catches all five broken traces, but turns the check binary |

**Config A's 0.92 measures whether the agent knows the tools exist.** A dashboard built on that default looks nearly perfect. It is missing a reversed
sequence, a silently dropped output and a wrong travel date, all at once.

Both extremes are wrong:

- **Too strict** fails a harmless extra call.
- **Too loose** passes an agent that fires every tool on every question.

**Demand strict ordering only where the order is itself the requirement** ([field guide, how strict the match is](../concepts/field-guide/05-conversations-tools-and-task-completion.md#23-how-strict-is-the-match)).

A selection check can also take the list of tools the agent *could* have called:

- **Without that list,** the check compares called tools to expected tools mechanically.
- **With it,** a judge also asks whether the agent picked the *best* available tool.

> **Turning that on makes a pure code check partly judged.** That is Level 0's cost ladder applied to a single metric.

### Argument correctness: cheap check first, judge second

"Were the arguments right?" is two questions with different prices:

- **Is it well-formed?** Code answers it, for free.
- **Does it make sense for the request?** Only a judge answers it.

Validate the schema first. Spend the judge call only if that passes ([field guide, two-pass argument checks](../concepts/field-guide/05-conversations-tools-and-task-completion.md#25-check-arguments-in-two-passes)).

```mermaid
flowchart LR
    C["Tool call"] --> V{"Schema valid?<br/>code check, free"}
    V -->|"No"| Z["Score 0<br/>judge never runs"]
    V -->|"Yes"| J["Judge: do the arguments<br/>fit the request?"]
    style Z fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

```python
# A structurally malformed call is worth zero -- no point spending a judge call
# to have a model tell you the date field isn't a date.
valid, reason = validate_args(test_case.tools_called)
if not valid:
    print(f"Score: 0\nReason: {reason}")   # judge never runs -- free rejection
else:
    metric.measure(test_case)              # now spend the LLM call
```

### Combine with the minimum, and score doing nothing

Two more rules come from the field guide's [sub-score and no-call rules section](../concepts/field-guide/05-conversations-tools-and-task-completion.md#26-combine-sub-scores-with-the-minimum):

- **Combine a selection score and an argument score with the minimum, not the mean.** Right tool plus nonsense arguments is a failed booking, not
  "half working".
- **Let the expected-tool list be empty.** Then restraint can pass ("What's your refund policy?" needs no call). A claimed action with no call behind
  it can fail.

---

## 3. Verify the Outcome, Not the Sentence

Everything in Section 2 judges mechanics. None of it asks what the user cares about: did the agent get the job done?

The gap runs in both directions:

- **Right calls, wrong outcome.** An agent can call every tool correctly and still book the wrong hotel, because it silently dropped a stated budget.
- **Imperfect path, fine outcome.** A slightly inefficient sequence can still land on a fine outcome.

A production suite needs both.

### Task completion as a judged check

A task-completion check is judged and referenceless: it needs no expected answer.

- **It reads three inputs.** The user's goal, the final answer and the list of tools called.
- **It asks one question.** Was the underlying task done?
- **Pass the tool list.** Some toolkits make it optional. Pass it anyway.

Take an agent that books a real, valid hotel reservation through well-formed calls, at $30/night over the user's stated $150 budget:

- **Selection and argument checks both score it well.** The tools were right and the arguments well-formed.
- **A task-completion check is built to catch the miss.** The actual requirement, staying under budget, was not met.

A constraint stated earlier in a conversation, like that budget, is what gets lost when the check infers the task from the last message. State the
task explicitly. The field guide's [task completion section](../concepts/field-guide/05-conversations-tools-and-task-completion.md#3-task-completion)
covers how to set the check up and its two escalations:

- **A custom rubric** when "done" is domain-specific.
- **Verifying the side effect** when the stakes are too high for a judge.

> **A state-based check cannot be fooled by a fluent-but-wrong response.** Use it as the pass/fail gate wherever a checkable outcome exists. Keep the
> judged check for the fuzzy parts.

### Reading the record beats every judged check

*"Your refund of $45 has been issued"* reads as confident and complete whether or not a refund happened. The order database, the booking system and
the ledger cannot be fooled that way. They hold the event itself, not a *description* of it.

> **Wherever a real side effect exists to check, reading it is the strongest signal in this level.** It is free and deterministic.

The **polite tool failure** hides underneath all of this:

- **The tool fails quietly.** It returns `found: false` or an empty payload instead of raising an error.
- **The model fills the gap.** It answers with an invented balance.
- **The judged checks miss it.** **Neither grounding nor task success reads the tool's own output.**
- **A deterministic check catches it.** Only a code check on the tool result sees the failure.

The field guide's [polite tool failure section](../concepts/field-guide/05-conversations-tools-and-task-completion.md#4-polite-tool-failure) walks it
end to end.

```mermaid
flowchart LR
    T["Tool returns<br/>found: false"] --> M["Model invents<br/>a balance"]
    M --> G["Grounding and<br/>task success: pass"]
    T --> D["Deterministic check<br/>on the tool result"]
    D --> F["Fail: caught"]
    style D fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

### When the output is a query, compare what it returns

Some tools take code the agent wrote. In a text-to-SQL skill, the agent writes a query, and the answer is whatever that query returns. **Do not judge
the SQL text. Judge the result.** Two correct queries can look nothing alike. Run the generated query and a reference query on the same data, then
compare the result sets:

- **Rows.** The same rows come back.
- **Values.** Each row holds the same values.
- **Order.** The rows come in the same order, where the question asked for one.

That check is deterministic and needs no judge. For a read-only system it is the closest thing to verifying a side effect.

Run the cheap checks first, and stop at the first failure:

| Check | Catches | Cost |
| --- | --- | --- |
| Parses | Malformed SQL | Free |
| Executes | Wrong table or column names, type errors | One query |
| Touches only governed views | Queries that bypass the curated, permission-checked layer to reach raw tables | Free (read the query plan or the table list) |
| Result set matches the reference | Wrong joins, filters, aggregations, time windows | Two queries |

```mermaid
flowchart LR
    P["Parses?"] -->|"yes"| E["Executes?"]
    E -->|"yes"| G["Only governed<br/>views?"]
    G -->|"yes"| R["Result set matches<br/>the reference?"]
    R -->|"yes"| OK["Pass"]
    P -->|"no"| X["Stop: fail"]
    E -->|"no"| X
    G -->|"no"| X
    R -->|"no"| X
    style OK fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

Restricting the agent to governed views also helps evaluation. It shrinks the space of plausible-but-wrong queries before anything has to be checked.

**When there is no reference query**, fall back to referenceless signals:

- **It runs.** The query executes.
- **It stays in bounds.** It touches only governed views.
- **Its size is plausible.** It returns a believable row count.
- **The answer matches.** The written answer reflects the rows that came back.

Say plainly that these are weaker. For a regulated domain, write reference queries for the most frequent question patterns. Do not rely on the
fallback.

---

## 4. Judge the Path, Not Only Where It Ended

Given a multi-step run, was the *path* any good, apart from where it ended up? An agent can go wrong on the way in three ways:

- **Extra steps.** It reaches the right answer in twice the steps.
- **Blind retries.** It retries instead of correcting the input.
- **Repeats.** It makes an identical call for no new information.

> **Sections 2 and 3 see none of that.** They read the final list of calls and the final answer, never the shape of the trace that produced them.

The standard approach has three moves:

- **Run the agent's loop to build a trace.** A **trace** is a step-by-step record of what was called, with what arguments, and what happened.
- **Hand the trace to a *separate* evaluation pass.** The agent never grades itself.
- **Score it against a gold trajectory.** A **gold trajectory** is the sequence a human decided ahead of time was correct.

```mermaid
flowchart LR
    A["Agent loop"] --> T["Trace:<br/>tool, arguments,<br/>result per step"]
    G["Gold trajectory<br/>decided by a human"] --> E["Separate<br/>evaluation pass"]
    T --> E
    E --> S["Scores"]
    style E fill:#D9E3DB,stroke:#2F6B4F,color:#0E2226
```

### The refund-agent scenario, and the nine checks against it

One deliberately messy trace exercises all nine checks at once: the support agent working the order-#4521 refund. Its five steps:

1. A typo'd order ID that fails.
2. A corrected retry that succeeds.
3. A policy lookup.
4. An identical, *redundant* repeat of that lookup.
5. The refund.

The refund really does change a mock order database. End-state verification has something real to check.

| # | Check | What it catches | Level in this trace |
| - | --- | --- | --- |
| 1 | **Tool selection accuracy** | Coverage only. Does the called set include every tool in the gold set? Loosest of the nine | Outcome |
| 2 | **Argument correctness** | Right tool, invalid or malformed arguments | Outcome |
| 3 | **Redundant calls** | A (tool, arguments) pair that already *succeeded* earlier in the same trace | Step |
| 4 | **Step-wise accuracy** | Fraction of steps that made real forward progress (succeeded *and* weren't redundant) | Step |
| 5 | **Task success rate** | The ground-truth outcome for this one run | Outcome |
| 6 | **Trajectory match (fuzzy)** | Successful tool *set* vs. gold set, ignoring order and retries | Outcome |
| 7 | **End-state verification** | Reads the mutated system of record directly, not the agent's own claimed answer | Outcome |
| 8 | **Recovery / self-correction rate** | After an error, did a *later* step call the same tool and succeed? | Step |
| 9 | **Cost / efficiency proxy** | Redundant calls and errors treated as waste; `1 - wasted/total` | Step |

### Five of these nine never move

Step-level and outcome-level checks have to run together. Cleaning the same trace one piece at a time shows which checks react to waste and which do
not:

| Trace variant | Steps | Redundant (#3) | Step-wise (#4) | Recovery (#8) | Cost/efficiency (#9) |
| --- | --- | --- | --- | --- | --- |
| As actually traced | 5 | 1 | 0.60 | 1.00 | 0.60 |
| Without the redundant call | 4 | 0 | 0.75 | 1.00 | 0.75 |
| Without the typo'd ID (nothing to recover from) | 4 | 1 | 0.75 | n/a | 0.75 |
| Minimal clean path | 3 | 0 | **1.00** | n/a | **1.00** |

- **Flat checks.** Checks **1, 2, 5, 6 and 7** stay flat and passing across all four variants. The agent used every tool it needed, and the refund
  really was recorded, waste or no waste.
- **Moving checks.** **Step-wise accuracy and cost/efficiency swing from 0.60 to 1.00** as the waste comes out.

> **Task success alone reports "pass" on the messiest version of the trace.** It says nothing about the wasted policy lookup or the wrong order ID,
> which together make up two of its five calls.

The two checks that cannot be fooled by a fluent sentence put Section 3's "read the record, not the string" rule into code:

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

Recovery returns `None`, never `1.0`, when there were no errors. That is Section 1's "unmeasured must never look like passed" rule again.

### Three traps

The field guide's [three traps section](../concepts/field-guide/06-agent-trajectory.md#6-three-traps) names three:

- **A selection scorer that scores 100% for calling everything.** Fail unexpected calls too.
- **Exact-sequence matching as the default.** Match fuzzily by default, and exactly only where order is the requirement.
- **Rewarding recovery on its own.** Pair it with step-wise accuracy.

### From a hand-built trace to a live system

Hand-computing all nine from a toy trace is how the checks get learned. On a running system the *questions* stay the same. Only the source of each
answer changes. The field guide's [live-system section](../concepts/field-guide/06-agent-trajectory.md#7-what-each-check-looks-like-on-a-live-system)
maps all nine to their production source.

**An untraceable agent is unevaluable.** Every request needs a span (one timed entry in a trace) per retrieval, per model call and per tool call,
carrying tokens and latency. Without those spans, none of the nine has anything to read.

---

## 5. Rehearse the Design-Round Follow-Ups

Four questions test this level directly. Each is a decomposition problem.

**"Per-turn quality is 95%, but the customer says conversations fall apart. Can both be true?"**

- **Strong answer.** Both are true. Section 1's table shows a uniform 95% failing about a quarter of five-turn conversations. Track *where*
  conversations first break, as well as the rate.
- **Weak answer.** It assumes the complaint must be about one hard category and proposes slicing by topic.

**"What kind of failure can only be seen across turns?"**

- **Strong answer.** Acting without consent. The final reply can pass every single-turn check and still be wrong, because the missing agreement lived
  in an earlier turn. Score complied / violated / stalled, not pass / fail.
- **Weak answer.** "Multi-turn failures are mostly about memory, so I'd add a context-retention check." That names the most benign member of the
  family and stops there.

**"How do you evaluate whether an agent took an efficient path, not just a correct one?"**

- **Strong answer.** Assert *properties* of the path (recovery, redundancy, ordering) rather than prescribing one gold sequence.
- **Weak answer.** It defines the expected tool sequence per test case and scores how closely the actual sequence matches. That encodes one path when
  several are valid. It then becomes a maintenance burden and gets loosened until it measures nothing.

**"The agent has five tools. What new evaluation risks does that create?"**

- **Strong answer.** The real risk is a check silently changing meaning. A check like "was a tool called when one was expected?" is correct for a
  one-tool agent and **passes a wrong-tool call once there are five**. Nothing turns red, and the check now certifies the failure. Scorers have a
  scope of validity a system can outgrow. Audit them whenever the agent gains a capability.
- **Weak answer.** It treats the change as "more combinations to test".
- **Wrong-tool is worse than no-tool.** A wrong tool returns data that is genuine, irrelevant and confidently presented. That is far more convincing
  to a user, and to a judge, than a missing answer.

---

## Key Takeaways

- Per-turn quality compounds. 95% a turn is 77% over five turns. Report the session-level number beside the turn-level one.
- Acting without consent has no single-turn representation. The three outcomes to score are complied, violated and stalled, never pass/fail.
- Choose tool-matching strictness deliberately: names-only matching scores 0.92 on six traces of which five are broken.
- Combine a selection score and an argument score with the minimum. Averaging lets a healthy dimension cover for a broken one.
- An empty expected-tool set is a real expectation. Restraint deserves a passing score, and a claimed action with no call deserves a failing one.
- Wherever a real side effect exists, reading the system of record beats every judged check, and it is free.
- Five of the nine trajectory checks never move as waste is removed. Step-level and outcome-level checks have to run together.
- An untraceable agent is unevaluable. Instrumentation is a precondition.

## Check Yourself

1. Turn-level quality is 95% and a customer says five-turn conversations fall apart. Who is wrong? **Neither. 0.95 to the fifth power is 0.774.
   Roughly a quarter of five-turn conversations fail. The dashboard is reporting in the wrong unit.**
2. An agent replies "I've opened a ticket for you" on turn one, unprompted. Which single-turn check catches it? **None. The reply is helpful, on-topic
   and grounded. The missing agreement lives between turns, and its absence has nowhere to show up.**
3. A conversation-level check runs against a single-turn interaction. What must it report? **"Not measured", never zero. An unmeasured check and a
   failed one must never look identical on a dashboard.**
4. Tool selection scores 1.0 and argument correctness scores 0.0. What is the combined score, and why? **0.0, the minimum. The booking failed. A mean
   of 0.5 would read as "half working" when nothing was.**
5. A suite only inspects calls that happened. Name the two failures it cannot see. **A tool called that wasn't needed, and a claimed action with no
   call behind it. Both need the expected set to be allowed to be empty.**
6. A tool returns `found: false` and the agent answers with a balance anyway. Which checks miss it? **Grounding and task success both, since neither
   reads the tool's own output. Only a deterministic check on the tool result sees it.**
7. Cleaning the waste out of a trace moves two of the nine checks and leaves five flat. What does that tell you about task success? **It reports
   "pass" on the messiest trace. Outcome checks cannot see waste. Step-level checks have to run alongside them.**
8. A one-tool agent's "was a tool called when expected?" check gains four more tools. What happens? **It starts passing wrong-tool calls. The check's
   scope of validity was outgrown, and nothing turns red to say so.**

---

## References

All content above was drawn only from material already in this repository. Nothing here was invented, and no external source was consulted. This page
is the restyled edition of `archive/roadmap-explainers-org/02-agents-tools-conversations-trajectories-outcomes.md`; its content is the same, with
library class names replaced by what each check does.

**Notebook:**

- `courses/01-rag-agent-tool-evaluation/08_MultiTurn_Conversational_Evaluation.ipynb`: the turn-list representation of a dialogue, the three
  multi-turn checks, and conversation simulation.
- `courses/01-rag-agent-tool-evaluation/09_Tool_Use_Evaluation.ipynb`: tool selection, argument correctness, multi-turn tool use, the two-pass
  argument-validation pattern, and the minimum-not-average design.
- `courses/01-rag-agent-tool-evaluation/10_Task_Completion_Evaluation.ipynb`: task completion, the budget-violation worked example, the custom-rubric
  escalation, and the case for state-based outcome verification.
- `courses/01-rag-agent-tool-evaluation/12_Agent_Trajectory_Evaluation.ipynb`: the nine trajectory checks, the refund scenario, and the
  `end_state_verified` / `recovery_rate` functions.

**Docs:**

- `docs/concepts/field-guide/05-conversations-tools-and-task-completion.md` and `docs/concepts/field-guide/06-agent-trajectory.md` (field guide
  parts 5–6, formerly Parts 2–3): the multi-turn arithmetic and consent/stalled framing, the
  tool-use properties, the task-completion escalation ladder, the "polite tool failure" mode, the nine trajectory checks, the three traps, and the
  hand-built-trace-to-live-system table. Sections 2–4 now link to these for the definitions rather than restating them.
- `docs/concepts/databricks-mlflow-evals.md`, Part 4: the conversation-success table used in Section 1.
- `docs/interactive-labs/04-tool-use-evaluation.html`: the six-trace, three-configuration strictness comparison used in Section 2 (its 0.92 / 0.83 /
  0.17 mean scores were independently recomputed against the page's own scoring logic before use here).
- `docs/interactive-labs/05-agent-trajectory-evaluation.html`: the four-variant table used in Section 4, and the observation that five of the nine
  checks never move across those variants.
- `docs/interview-prep/QUESTION_BANK.md`, Part 7 (Q26–Q29): the four questions reproduced in full in Section 5 rather than pointed at.
- `docs/study-guide/evaluation-roadmap.md`: Level 2's topic list and goal statement.
- `docs/study-guide/evaluation-topic-notebook-mapping.md`: Level 2's resource table.
- `archive/labs-multiturn-and-tool-eval/README.md`: checked and found to introduce no topic beyond what course 01 already covers.

**Limitations.** Written from the repository's own material without running any notebook or calling any API. The percentage figures in Section 2's
strictness table and Section 4's trajectory-variant table were recomputed by hand against the scoring logic in each interactive lab's own source, not
copied from a live run. It does not verify any vendor's documentation.

---

**Next:** [Level 3, Ground Truth: Where Cases and Labels Come From](03-ground-truth.md) · **Previous:** [Level 1, RAG: Retrieval and Generation](01-rag-retrieval-and-generation.md)
