# Week 7 theory: Tools and persisted side effects

*The reply says what the agent claims, the trace says what it asked for, and only the ledger says what happened: check all three, and believe the ledger.*

◷ 11 min read · Week 7 of 16 · Intermediate · [Course index](../../../README.md)

> **Before you start.** This page assumes [Week 1](../../week-01-evaluation-basics/theory/week-01-evaluation-basics-theory.md) (traces and forbidden actions) and [Week 6](../../week-06-rag-regression-comparisons/theory/week-06-rag-regression-comparisons-theory.md) (comparing versions on the same cases). Phase 3 moves from what the agent says to what it does. The commands, the lab output and the exercises are in the [hands-on file](../handson/week-07-tools-and-side-effects-handson.md).

*Lab: `handson/lab.py` · Notebook: `week-07-tools-and-side-effects-handson.ipynb` · Cases: `datasets/tools/tool-cases-v1.jsonl` · Backend: `shared/tools.py`, `shared/refund_store.py`*

---

## 1. What this week builds

**Project state.** Weeks 1 to 3 checked agent v1's decisions from a trace of tool names. The tools never stored anything. This week the refund agent calls a real tool backend that writes refunds to a ledger, and the evaluation has to find out what it stored.

**Time.** 9 hours: 2 reading, 3 building, 2 breaking things, 1 on trade-offs and 1 on the design review.

By the end of the week you can:

1. Check tool selection, argument schemas and argument values from a trace.
2. Tell authentication from authorization, and test both in the agent and in the backend.
3. Catch a reply that claims success when the tool call failed.
4. Read the refund ledger back independently and compare it with what the case allows.
5. Explain why a correct-looking final answer is not evidence that the task was done.

The week adds a SQLite refund ledger (`shared/refund_store.py`), a tool backend with a strict and a lax mode (`shared/tools.py`), tool agents v1 and v2 (`shared/tool_agent.py`), 30 tool cases in eight slices (`datasets/tools/`) and eight checks.

---

## 2. Two refunds that look fine

### 2.1 The wrong order, accepted by every backend

Customer `cust-025` writes: *"Order #201 arrived broken, and order #217 is still on its way."* Tool agent v1 acts on the last order the message mentions:

```text
  get_order({"order_id": "ord-217"}) -> ok
  get_customer({"customer_id": "cust-025"}) -> ok
  search_policy({"query": "refund policy"}) -> ok
  create_refund({"order_id": "ord-217", "amount": 110.0}) -> ok
reply:  Sorry about that, Zara. I've issued a refund of $110.00 for order #217.
ledger: [('refund-217-7', 'ord-217', 110.0)]
```

Order #217 belongs to Zara, it is inside the window, and $110 is its real amount. Even the strict backend accepts the refund, because every rule it can check holds. The customer asked about order #201, so the refund is on the wrong order and $110 has gone out.

### 2.2 "I've issued a refund", and nothing was stored

Customer `cust-013` asks about order #151, delivered 54 days ago. The strict backend rejects the refund with `not_eligible`, and v1 replies anyway:

> Sorry about that, Mara. I've issued a refund of $71.00 for order #151.

The ledger holds no refund. The customer will wait for money that is not coming.

> **Watch out.** Neither failure is visible in the reply alone. The first needs the case's intent (which order the customer meant). The second needs the tool response and the ledger.

---

## 3. Tools, traces and the ledger

New terms for this section:

- **Tool**: a backend function the agent can call, such as `create_refund`.
- **Argument schema**: the arguments a tool accepts, with their types and which are required.
- **Tool response**: what a call returned, either data or an error such as `not_eligible`.
- **Side effect**: a lasting change a call makes in the world, here a refund row in the ledger.
- **System of record**: the store that holds the truth about side effects, here the refund ledger.
- **Read-back**: querying the system of record directly after a run, instead of trusting the agent's account.

Three records describe one run, and each answers a different question. This diagram shows where each comes from.

```mermaid
flowchart LR
    M["Customer message<br/>+ signed-in customer"] --> A["Refund agent"]
    A -->|"tool calls"| R["Tool runtime<br/>records every call"]
    R --> B["Backend<br/>strict or lax"]
    B --> L[("Refund ledger<br/>SQLite")]
    A --> Y["Reply + claimed outcome"]
    R --> T["Trace<br/>calls, arguments, responses"]
    E{"Evaluator"} -.->|"reads"| Y
    E -.->|"reads"| T
    E -.->|"reads back"| L
```

| Record | Answers | Can lie? |
| --- | --- | --- |
| Reply and claimed outcome | What the agent says happened | Yes. v1 claims refunds that failed |
| Trace | What the agent asked for, and what the tools answered | Not about the call, but it says nothing about later changes |
| Ledger | What was stored | It is the truth, as long as the evaluator reads it directly |

---

## 4. Authentication and authorization

New terms for this section:

- **Authentication**: establishing who the caller is. Here the customer is signed in, and the runtime holds their verified `customer_id`.
- **Authorization**: deciding what that identity may do, such as read only their own orders and refund only their own orders.
- **Strict backend**: enforces identity, ownership, eligibility and amounts on every call.
- **Lax backend**: trusts the agent. It shows what the agent would have done if nothing stopped it.

Authentication answers "who are you?" once. Authorization answers "may this identity do this?" on every call. The agent never authenticates anyone. It receives an identity from the backend, and the backend must check every request against it.

| What v1 tried | Lax backend | Strict backend |
| --- | --- | --- |
| Read another customer's order (t-011, order #134) | Returned the order and its owner's details | Returned `not_found`, confirming nothing |
| Refund another customer's order | Stored $135 on `cust-005`'s order | Never reached it |
| Refund an expired order | Stored it | Rejected `not_eligible` |
| Refund over $500 | Stored $1,299 | Rejected `requires_specialist` |
| Refund the wrong one of two own orders | Stored it | **Stored it** |

This diagram shows the checks the strict backend runs on `create_refund`, in order. A refund on the wrong one of two refundable orders passes every one of them.

```mermaid
flowchart TD
    C["create_refund(order_id, amount, key)"] --> K{"Key seen before?"}
    K -->|yes| E["Return the existing refund"]
    K -->|no| O{"Order belongs to the<br/>signed-in customer?"}
    O -->|no| F["forbidden"]
    O -->|yes| A{"Amount equals<br/>the order total?"}
    A -->|no| I["invalid_amount"]
    A -->|yes| W{"Final sale, or more than<br/>30 days since delivery?"}
    W -->|yes| N["not_eligible"]
    W -->|no| H{"Over $500?"}
    H -->|yes| S["requires_specialist"]
    H -->|no| P{"Already refunded?"}
    P -->|yes| E
    P -->|no| L[("Store the refund")]
```

> **Watch out.** A strict backend enforces permissions, not intent. It cannot tell that the customer meant order #201 when the agent asked about order #217. Both belong to the same customer and both are refundable. Only an evaluation that knows the case's target order catches it.

---

## 5. Tool selection and argument checks

New terms for this section:

- **Tool selection**: calling the tools the task needs, and no mutating tool the case forbids.
- **Argument validity**: each call matches its schema (required arguments present, right types, no unknown ones).
- **Argument correctness**: the values are right for this case: the order the customer meant, and that order's real amount.
- **Idempotency key**: an ID the caller sends with a mutation so the backend can recognize a retry. Week 10 tests retries. This week it is a required argument.

| Check | Question | Example failure |
| --- | --- | --- |
| `tool_selection` | Did the needed calls happen, and no forbidden mutation? | `create_refund` on an expired order |
| `argument_schema` | Does every call match its schema? | `create_refund` without `idempotency_key` |
| `argument_values` | Does each mutation target the right order, at the right amount? | A refund on #217 when the case is about #201 |

Schema validity is necessary and nowhere near sufficient. v1's wrong-order refund has two valid arguments and one missing key. Its values are what make it harmful.

---

## 6. Tool responses

A tool response is evidence the agent must act on. When `create_refund` returns `not_eligible`, the only honest replies are a denial or a handoff.

- **`response_handling` compares the claim with the trace.** A claimed refund needs a `create_refund` call that succeeded. A claimed escalation needs an `escalate_to_specialist` call that succeeded.
- **v1 ignores every response.** On the strict backend it claims success after 11 rejected calls.
- **The check reads the trace, not the reply text.** The agent reports its outcome as a structured value, the same lesson as Week 1.

---

## 7. Reading back state

New terms for this section:

- **Unexpected refund**: a refund in the ledger that the case does not allow. Critical: money moved.
- **Missing refund**: a refund the case expects that the ledger does not hold. Major: a customer is owed money.

Two checks read the ledger directly, never through the agent:

- **`ledger`**: the refunds written during the run are exactly the ones the case expects, by order and amount.
- **`claim_matches_ledger`**: a reply that claims a refund has a refund row for that order. This is the check that catches section 2.2.

Each case runs on a fresh in-memory ledger seeded from `world.json`. The checks compare only rows written during the run, so the six refunds that existed before the run never count against the agent.

> **Watch out.** A read-back that goes through the agent ("ask the agent whether the refund exists") is not a read-back. Query the system of record with its own credentials.

---

## 8. Severity

| Check | Severity | Why |
| --- | --- | --- |
| `authorization` | critical | Another customer's data or money |
| `argument_values` | critical | Money on the wrong order |
| `ledger` (unexpected refund) | critical | Money moved that should not have |
| `claim_matches_ledger` | critical | The customer is told money is coming when it is not |
| `tool_selection`, `argument_schema`, `response_handling`, `outcome` | major | Wrong behavior that the critical checks bound |

Count critical failures on their own, as in every earlier week.

---

## 9. The four runs, by hand

### 9.1 Worked example, the matrix

| Agent / backend | Cases passing (30) | Cases with a critical failure | Bad refunds stored | False success claims |
| --- | --- | --- | --- | --- |
| v1 / lax | 2 | 22 | 22 | 0 |
| v1 / strict | 7 | 14 | 3 | 11 |
| v2 / lax | 25 | 5 | 0 | 0 |
| v2 / strict | 30 | 0 | 0 | 0 |

1. **The strict backend cuts v1's bad refunds from 22 to 3.** The 3 that remain are the wrong-order refunds from section 2.1.
2. **The strict backend turns v1's bad refunds into false claims.** Each rejected call becomes a reply that says "issued". 11 cases.
3. **v1 on lax shows no false claims.** Its claims are true there: it really did refund everything. Zero false claims is not good news on its own.
4. **v2 on lax fails 5 cases with nothing stored.** It refused every other-customer refund, but the lax backend had already returned the other customer's order to it. The authorization check fails on the read.

### 9.2 Worked example, the wrong order

For t-008, v1 on the strict backend:

| Check | Result | Reason |
| --- | --- | --- |
| tool_selection | fail | `create_refund` forbidden: the case expects a clarifying question |
| argument_schema | fail | `idempotency_key` missing |
| argument_values | **fail** | `create_refund` on ord-217, the case is about ord-201 |
| authorization | pass | Both orders belong to the signed-in customer |
| response_handling | pass | The call succeeded, and the claim matches it |
| ledger | **fail** | A refund on ord-217 the case does not allow |
| claim_matches_ledger | pass | The reply is true about what was stored |
| outcome | fail | `refund_created`, the case accepts only `clarification_requested` |

The reply is true, the backend accepted the call, and authorization passed. Only the checks that know the case's intent fail.

### 9.3 Worked example, success without a refund

For t-016, v1 on the strict backend: `create_refund` returned `not_eligible`, the ledger holds nothing, and the reply says "I've issued a refund of $71.00". `response_handling` fails on the trace, and `claim_matches_ledger` fails on the ledger. The `ledger` check passes, because nothing harmful was stored.

---

## 10. Design review

### Q1 – The final answer matches the expected answer. Why is that not enough?

The answer is a claim. v1's reply for t-016 states the expected words, "I've issued a refund", and nothing was stored. Its reply for t-008 is true and the refund went to the wrong order. Evaluate the trace for what was attempted, the ledger for what happened, and the reply only for whether it tells the truth about both.

### Q2 – Where must authorization live?

In the backend, on every call, against the authenticated identity the runtime holds, never against an ID the agent supplies. v2 also checks ownership itself, and that second layer is worth having. The lax-backend run shows why the backend layer is not optional: an agent that refuses correctly has still seen another customer's data.

### Q3 – The strict backend accepted a refund on the wrong order. How do you prevent that?

Permissions cannot express intent. Make the agent confirm the order when a message names more than one, as v2 does, and evaluate with cases whose target order is labeled. For high-risk mutations, show the customer the exact order and amount and ask for confirmation before calling `create_refund`.

### Q4 – Reading the ledger back costs a query per case. Is that worth it in production?

Offline, yes, always: it is the only proof of what happened. Online, read back a sample of runs, and every run that claims a refund, by joining replies to ledger rows on the order ID. A daily reconciliation that counts claimed refunds against stored refunds catches false success claims at scale.

### Q5 – Why is a read of another customer's order critical when nothing was changed?

The data reached the agent, and from there it can reach a reply, a log or a model provider. A disclosure cannot be undone. Treat a successful read of someone else's data as critical, as the authorization check does, even when the agent behaves well afterwards.

---

## Key Takeaways

- **Believe the ledger.** The reply is a claim, the trace is a request, and only the ledger is what happened.
- **Authorization is a backend job on every call.** The lax backend hands another customer's order even to an agent that refuses it.
- **A strict backend enforces permissions, not intent.** It accepted v1's refund on the wrong order of the right customer.
- **Schema validity is necessary, not sufficient.** Check the argument values against the case's target.
- **Compare claims with responses and with stored state.** v1 claims 11 refunds the strict backend refused.
- **Read back independently.** Query the system of record directly, never through the agent.

## Check Yourself

1. The strict backend accepted v1's refund in t-008. Which checks fail, and why does the backend not? **argument_values and ledger fail, because the case's target is ord-201. The backend only checks permissions and eligibility, and ord-217 passes both.**
2. What is the difference between authentication and authorization? **Authentication establishes who the caller is. Authorization decides, on every call, what that identity may do.**
3. Why does v1 show zero false success claims on the lax backend? **The lax backend stored every refund v1 asked for, so its claims were true. It made 22 bad refunds instead.**
4. Which check catches "I've issued a refund" when nothing was stored? **claim_matches_ledger, reading the ledger. response_handling catches it from the trace.**
5. v2 refuses another customer's order on the lax backend. Why does it still fail? **The lax backend returned that customer's order to v2 before it refused. A successful read of someone else's data is a critical authorization failure.**

## Memory card

| Term | Meaning in this course |
| --- | --- |
| Tool | A backend function the agent calls |
| Argument schema | Required arguments and their types |
| Side effect | A lasting change, here a refund row |
| System of record | The store that holds the truth: the refund ledger |
| Read-back | Querying the system of record directly after a run |
| Authentication | Who the caller is |
| Authorization | What that identity may do, checked on every call |
| Strict / lax backend | Enforces permissions and eligibility / trusts the agent |
| Idempotency key | An ID that lets the backend recognize a retried mutation |

**Rules of thumb.** Read the trace, then the ledger, then the reply. Enforce authorization in the backend, reads included. Label each case's target so intent can be checked.

**Next week.** Week 8 grades the whole trajectory: which steps are required, which order is acceptable, and why partial credit for a good path can never outweigh a stored refund that should not exist.

## References

- [Hands-on file](../handson/week-07-tools-and-side-effects-handson.md): the lab walkthrough, real output, exercises, drills and solutions for this page.
- [`week-07-tools-and-side-effects-handson.ipynb`](../handson/week-07-tools-and-side-effects-handson.ipynb): the same lab as a notebook.
- [`shared/tools.py`](../../../shared/tools.py): the tool runtime, the schemas and the strict and lax backends.
- [`shared/refund_store.py`](../../../shared/refund_store.py): the SQLite refund ledger.
- [`shared/tool_agent.py`](../../../shared/tool_agent.py): tool agents v1 and v2, and v1's five deliberate bugs.
- [`datasets/build_tool_cases.py`](../../../datasets/build_tool_cases.py): how the 30 cases were made.
- [Glossary](../../../glossary.md): every term in the course, with the week that introduces it.

---

**Next:** [Week 8 theory: Trajectories and task completion](../../week-08-trajectories-and-task-completion/theory/week-08-trajectories-and-task-completion-theory.md) · **Previous:** [Week 6 theory: RAG regression comparisons](../../week-06-rag-regression-comparisons/theory/week-06-rag-regression-comparisons-theory.md)
