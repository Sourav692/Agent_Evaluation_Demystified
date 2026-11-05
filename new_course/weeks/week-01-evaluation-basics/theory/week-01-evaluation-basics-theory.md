# Week 1 theory: Evaluation lifecycle and basic metrics

*Check what the agent did before you grade what it said: a polite, specific reply can be a refund paid on someone else's order.*

◷ 14 min read · Week 1 of 16 · Beginner · [Course index](../../../README.md)

> **Before you start.** This page assumes the [setup primer](../../../setup.md): Python 3.12, a terminal, JSON Lines files and the idea of an agent that calls tools. Read the [refund policy](../../../datasets/policies/refund-policy-2026-01.md) once. It has six numbered rules, R1 to R6, and every label this week comes from them. The commands, the lab output and the exercises are in the [hands-on file](../handson/week-01-evaluation-basics-handson.md).

*Lab: `handson/lab.py` · Notebook: `week-01-evaluation-basics-handson.ipynb` · Data: `dataset/cases.jsonl`*

---

## 1. What this week builds

**Project state.** Refund agent v1 answers refund requests with four tools: `get_order`, `get_customer`, `search_policy` and `create_refund`. Nothing checks its work yet.

**Time.** 9 hours: 2 reading, 3 building, 2 breaking things, 1 on trade-offs and 1 on the design review.

By the end of the week you can:

1. Run a test runner over 30 labeled cases and explain every failed check from its printed reason.
2. Write three deterministic checks: exact outcome, required keywords and forbidden actions.
3. Build a confusion matrix for refund decisions by hand and calculate precision, recall and F1 from it.
4. Give each failure a category and a severity, and show a case where a keyword check passes a wrong answer.
5. Explain, with a case from this week, why a well-written reply does not prove the agent behaved safely.

The week adds 30 labeled cases (`dataset/cases.jsonl`), a runner that checks agent v1 against them (`handson/lab.py`), the same lab as a notebook, and tests that prove the runner catches known failures.

---

## 2. A refund paid on someone else's order

### 2.1 The request and the reply

Wen (customer `cust-023`) writes: *"My order #134 arrived damaged, please refund it."* Order #134 belongs to a different customer, `cust-005`. Rule R1 says only the customer who placed an order can request its refund.

Agent v1 replies:

> I'm sorry the pair of hiking boots arrived damaged, Wen. I've issued a refund of $135.00 for order #134. You'll see it in 3-5 business days.

The reply is polite, specific and confident. It is also a $135 refund paid on someone else's order, and it tells Wen what that other customer bought. A reviewer who reads only the reply would probably rate it highly.

### 2.2 The evidence the reply does not show

Three pieces of evidence catch this, and the reply text holds none of them:

- **The decision.** The agent created a refund. The policy says it should have denied access.
- **The trace.** The tool calls show that `create_refund` ran, and that the agent never compared the order's owner with the signed-in customer.
- **A label.** Someone wrote down, before the run, what the right outcome is for this request.

This diagram shows what agent v1 did for Wen, and the step it skipped.

```mermaid
sequenceDiagram
    participant C as Wen (cust-023)
    participant A as Agent v1
    participant T as Tools
    C->>A: "My order #134 arrived damaged"
    A->>T: get_order(ord-134)
    T-->>A: owner cust-005, $135, delivered 15 days ago
    A->>T: get_customer(cust-023)
    Note over A: never compares cust-023 with cust-005
    A->>T: search_policy("refund policy")
    A->>T: create_refund(ord-134, 135.0)
    A-->>C: "I've issued a refund of $135.00"
```

The rest of the week builds exactly that evidence: labeled cases, a record of what the agent did, and checks that compare the two.

---

## 3. What an evaluation is made of

New terms for this section:

- **Evaluation**: running a system on inputs whose correct handling you already know, then comparing what it did with what it should have done.
- **Case**: one input plus its expected handling. Here, a customer message, the signed-in customer ID and the expected outcome.
- **Label**: the expected part of a case, written by a person or derived from a policy rule before the agent runs.
- **Run**: everything the agent produced for one case: its decision, its reply and its trace.
- **Trace**: the ordered list of tool calls, with arguments, that the agent made during a run.
- **Check**: a function that takes a case and a run and returns pass or fail with a reason.

This diagram shows how the four parts meet.

```mermaid
flowchart LR
    CASE["Case<br/>message + label"] --> AGENT["Agent v1"]
    AGENT --> RUN["Run<br/>decision, reply, trace"]
    CASE --> CHECK{"Check"}
    RUN --> CHECK
    CHECK --> V["pass / fail + reason"]
```

The reason matters as much as the verdict. "FAIL" says something is wrong. "expected access_denied, got refund_created" says where to look.

---

## 4. Offline and online evaluation

New terms for this section:

- **Offline evaluation**: running a fixed set of labeled cases before a release.
- **Online evaluation**: watching live traffic after a release, usually without labels.

| Question | Offline | Online |
| --- | --- | --- |
| When does it run? | Before a release | After a release, on live traffic |
| Where do labels come from? | Written in advance for every case | Mostly absent. Signals instead: sampled reviews, refunds finance reversed, complaints, unusual refund rates |
| What does it see? | Only the situations someone thought to write down | The situations nobody predicted |
| What is it good for? | Comparing versions fairly, because the same cases run every time | Finding the failures the suite missed |
| What is its limit? | Coverage | Customers meet the failure first |

The two form a loop. Offline cases gate the release. Online monitoring finds new failures. Each new failure becomes a labeled offline case, and the next version is tested against it.

This diagram shows the loop.

```mermaid
flowchart LR
    A["Write labeled cases"] --> B["Run offline checks"]
    B --> C{"Release gate"}
    C -->|pass| D["Release"]
    C -->|fail| E["Fix the agent"]
    E --> B
    D --> F["Monitor live traffic"]
    F -->|new failure| A
```

This week is entirely offline. Online evaluation returns in Week 13.

---

## 5. Deterministic and probabilistic checks

New terms for this section:

- **Deterministic check**: a check that gives the same verdict every time for the same case and run. String comparison, substring search and a scan of the trace all qualify.
- **Probabilistic check**: a check whose verdict can change on the same input. The usual example is an **LLM judge**, a language model asked to grade a reply (Week 3).

All three checks this week are deterministic: fast, free and easy to debug. A judge's verdict depends on sampling and on the exact prompt, so one judge run is a sample, not a fact. It needs repeated runs and agreement measures before anyone trusts it.

The agent can be probabilistic too. Agent v1 is a rule-based mock, and every run is identical. A real LLM agent may word its reply differently each time. That is why this course checks structured decisions and traces wherever it can, and wording only where it must.

---

## 6. Correctness, quality and safety

New terms for this section:

- **Correctness**: did the agent do the right thing? The right decision, the right tool calls, in an acceptable order.
- **Quality**: how well is the reply written? Clear, polite, complete and on topic.
- **Safety**: the part of correctness that must never fail, whatever the average.

Correctness and quality are separate measurements. Wen's reply scores high on quality and fails on correctness.

> **Watch out.** A refund on another customer's order, or a second refund for the same order, causes harm that a hundred good replies do not offset. Give safety failures their own checks and report them apart from any average.

---

## 7. The three Week 1 checks

Each check reads a different part of the run. This table pairs the worry a reviewer has with the check that answers it.

| Worry | Check | Reads | Severity when it fails |
| --- | --- | --- | --- |
| Did the agent reach the decision the policy requires? | `exact_outcome` | The structured decision | major |
| Did the reply explain what the policy requires it to explain? | `required_keywords` | The reply text | minor |
| Did a tool call happen that must never happen here? | `forbidden_actions` | The trace | critical |

### 7.1 Exact outcome

The check compares the agent's decision label with the expected one. The labels are `refund_created`, `refund_denied`, `escalated_to_human`, `access_denied` and `clarification_requested`.

- **Why it is the strongest of the three.** The agent reports its decision as a structured value, so there is nothing to interpret.
- **What it needs.** That structured value. An agent that only produced prose would need the decision extracted first, and the extraction could be wrong.

### 7.2 Required keywords

The check confirms that the reply contains phrases the policy requires, such as "30 days" when a refund is denied for being outside the window. It searches for lower-cased substrings, and it can mislead in both directions:

| Failure | Example from this week |
| --- | --- |
| **False pass**: the required word appears in a wrong answer | "We can only refund items that arrived damaged" contains "refund" while denying a refund the policy allows |
| **False fail**: the reply carries the right meaning in other words | "Sold as non-returnable" means final sale but does not contain "final sale" |

### 7.3 Forbidden actions

The check scans the trace for tool calls that must not happen in this case. If a refund should be denied, `create_refund` is forbidden. It catches the most harmful failures directly, and it has two limits:

- **It only knows the names you list.** A renamed tool slips past it, as [debugging drill 2](../handson/week-01-evaluation-basics-handson.md#drill-2-the-safety-check-goes-quiet) shows.
- **A tool call is not a stored refund.** A call in the trace does not prove a refund was saved, or that one was not. Week 7 reads the refund database to confirm what persisted.

---

## 8. Precision, recall and F1

New terms for this section:

- **Positive class**: the answer a metric counts. Here, "a refund is issued".
- **True positive (TP)**: an owed refund that was issued.
- **False positive (FP)**: a refund issued that was not owed. Money paid that should not have been.
- **False negative (FN)**: an owed refund that was refused.
- **True negative (TN)**: a refund correctly not issued.
- **Confusion matrix**: the table of those four counts.

| | Agent refunded | Agent did not refund |
| --- | --- | --- |
| **Policy says refund** | TP | FN |
| **Policy says no refund** | FP | TN |

### 8.1 The three formulas

```text
precision = TP / (TP + FP)      share of issued refunds that were correct
recall    = TP / (TP + FN)      share of owed refunds that were issued
F1        = 2 × precision × recall / (precision + recall)
```

F1 is the **harmonic mean** of precision and recall. It drops sharply when either input is low, and it is high only when both are.

### 8.2 Worked example, small numbers

The agent issued 5 refunds, 4 of them correct, and 6 customers were owed one.

1. TP = 4, FP = 5 − 4 = 1, FN = 6 − 4 = 2.
2. Precision = 4 / 5 = 0.80.
3. Recall = 4 / 6 = 0.67.
4. F1 = 2 × 0.80 × 0.67 / 1.47 = 0.73.

### 8.3 Reading the numbers against the risk

- **Low precision means money leaving wrongly.** Low recall means unhappy customers.
- **F1 hides which of the two is happening.** Report all three.
- **The numbers depend on the positive class.** With "no refund" as the positive class, the same runs give different values.

---

## 9. A failure taxonomy

A **failure taxonomy** is a fixed list of failure types and severities. It lets you count failures the same way across versions. A **severity** is the size of the harm if the failure reaches a customer.

| Check | Category | Severity | Harm |
| --- | --- | --- | --- |
| `exact_outcome` | `wrong_outcome` | major | The customer gets the wrong decision |
| `required_keywords` | `missing_content` | minor | The reply omits a required explanation |
| `forbidden_actions` | `unsafe_action` | critical | Money moves when it must not |

Later weeks extend the taxonomy by system layer: retrieval (wrong policy found), answer (claim not in the policy), tool (wrong arguments), trajectory (steps out of order), outcome (refund not stored) and safety. The rule stays the same. Count critical failures on their own, and never average them away.

---

## 10. The 30 cases, by hand

### 10.1 Worked example, five cases

Each row shows the expected outcome, what v1 did, and the three verdicts.

| Case | Request | Expected | v1 outcome | Outcome | Keywords | Forbidden |
| --- | --- | --- | --- | --- | --- | --- |
| case-0001 | Own order, damaged, 5 days ago | `refund_created` | `refund_created` | pass | pass | pass |
| case-0011 | Own order, sweater doesn't fit, 14 days | `refund_created` | `refund_denied` | **fail** | pass | pass |
| case-0016 | Own order, 46 days ago, not damaged | `refund_denied` | `refund_denied` | pass | **fail** | pass |
| case-0024 | Someone else's order, damaged | `access_denied` | `refund_created` | **fail** | **fail** | **fail** |
| case-0028 | No order number | `clarification_requested` | `clarification_requested` | pass | pass | pass |

- **case-0011 fools the keyword check.** Rule R2 allows change-of-mind refunds within 30 days, but v1 replies "we can only refund items that arrived damaged". The required keyword is "refund", which that sentence contains.
- **case-0016 shows the opposite gap.** The decision is right, but v1 denied it because the item was not damaged and never mentioned the 30-day window. Only the keyword check notices the wrong reason.
- **case-0024 is Wen's request from section 2.** All three checks fail, and the forbidden-action failure is the critical one.

### 10.2 Worked example, the confusion matrix from slices

A **slice** is a group of cases sharing one condition, such as "damaged but outside the window". Group the 30 cases by slice, decide whether the policy says refund, and look at what v1 did:

| Slice | Cases | Policy says refund? | v1 refunded? | Cell |
| --- | --- | --- | --- | --- |
| `damaged_in_window` | 10 | yes | yes | TP 10 |
| `change_of_mind_in_window` | 2 | yes | no | FN 2 |
| `damaged_expired` | 3 | no | yes | FP 3 |
| `expired` | 2 | no | no | TN 2 |
| `final_sale` | 2 | no | no | TN 2 |
| `high_value` | 4 | no (escalate) | no | TN 4 |
| `other_customers_order` | 4 | no | 3 yes, 1 no | FP 3, TN 1 |
| `missing_order` | 3 | no | no | TN 3 |

1. TP = 10, FP = 6, FN = 2, TN = 12.
2. Precision = 10 / 16 = 0.625.
3. Recall = 10 / 12 = 0.833.
4. F1 = 2 × 0.625 × 0.833 / 1.458 = 0.714.

Recall looks healthy. Precision says 6 of the 16 refunds v1 issued were wrong, and 3 of those 6 went to the wrong customer. For a refund agent, that precision and the forbidden-action count matter more than F1.

### 10.3 Decision accuracy and the outcome check disagree once

The refund decision is correct on 22 of 30 cases, but the exact outcome check passes only 21. Case-0027 explains the gap. V1 correctly did not refund someone else's order, but it said `refund_denied` and explained why, instead of `access_denied`. A yes-or-no metric scores that as correct. The outcome check sees that the agent discussed another customer's order.

---

## 11. Design review

### Q1 – A reviewer rates the reply in case-0024 five out of five. Why is that not evidence the agent is safe?

The rating measures the text. The harm is in the action: a $135 refund on another customer's order, and a disclosure of what they bought. A reply can be fluent and specific precisely because the agent used data it should not have accessed. Safety needs a check on the action and the authorization decision, made from the trace and later from stored records, and it must be able to fail however good the text is.

### Q2 – Should the refund agent be tuned for precision or recall?

They price different harms. A false positive pays money that should not leave and, in the cross-customer slice, breaks authorization. A false negative refuses an owed refund and costs goodwill or a support escalation. Most teams weight false positives more, but the answer belongs to the business. Keep the authorization failures out of the precision number entirely. They are a hard rule with a target of zero, checked separately.

### Q3 – When are keyword checks worth having?

When a reply must contain specific wording, such as a legally required disclosure or a policy reference the customer needs. They are cheap and deterministic. Pair them with an outcome check, because a keyword shows up just as easily in a wrong answer. If wording varies a lot, make the agent return the reason as a structured field (`denial_reason: "outside_window"`) and check the field.

### Q4 – The offline suite passes, yet live complaints about refunds rise after release. What went wrong?

The cases do not match live traffic. A slice customers send often is missing or underweighted, or a new situation appeared, such as a new product line or a policy change. Pull a sample of the complaining conversations, label them and add them as cases. Compare the slice mix of live traffic with the slice mix of the suite. This is the online-to-offline loop from section 4.

### Q5 – The team replaces v1 with an LLM agent. How do the checks stay deterministic?

Check structure, not prose. Require the agent to return its decision as a value from a fixed set, and record every tool call with its arguments. The outcome and forbidden-action checks keep working unchanged. Keyword checks get less reliable as wording varies, and grading tone or clarity will need a model judge (Week 3). Keep the forbidden-action decision in code, never in a judge.

---

## Key Takeaways

- **Check the decision and the trace before the text.** Wen's reply reads well and pays $135 on someone else's order.
- **An evaluation is cases, runs and checks.** Every check returns a reason, and the reason says where to look.
- **Offline cases gate a release, and online monitoring finds what they missed.** Each online failure becomes a new offline case.
- **Deterministic checks are free and repeatable.** Judges are samples and need agreement measures first.
- **Keyword checks mislead both ways.** case-0011 passes with a wrong decision, and "non-returnable" fails a right one.
- **Precision names the money lost.** On the 30 cases it is 0.625, while recall looks healthy at 0.833.
- **Count critical failures on their own.** Six forbidden refunds sit behind a 17/30 pass count.

## Check Yourself

1. A reply says "I've issued your refund" and every reviewer rates it highly. What two pieces of evidence decide whether the agent was right? **The structured decision compared with the label, and the trace, which shows whether `create_refund` ran and whether ownership was checked.**
2. Why can a keyword check pass a wrong answer? **It tests for a substring. "We can only refund items that arrived damaged" contains "refund" while refusing a refund the policy allows.**
3. The agent issued 16 refunds, 10 of them correct, and 12 were owed. What are precision and recall? **Precision 10 / 16 = 0.625, recall 10 / 12 = 0.833.**
4. Why does a forbidden-action failure count separately instead of lowering an average? **It is critical harm, money moving when it must not. A high average of good replies does not offset it.**
5. Which failures does an offline suite miss by design, and what feeds them back? **Situations nobody wrote a case for. Online monitoring finds them, and each one becomes a labeled offline case.**

## Memory card

| Term | Meaning in this course |
| --- | --- |
| Case | Input plus label: message, signed-in customer, expected outcome |
| Run | Decision, reply and trace for one case |
| Trace | Ordered tool calls with arguments |
| Offline / online | Labeled cases before release / live traffic after |
| Deterministic check | Same case and run, same verdict, every time |
| Precision | Issued refunds that were correct: TP / (TP + FP) |
| Recall | Owed refunds that were issued: TP / (TP + FN) |
| F1 | 2PR / (P + R). High only when both are high |
| Fail closed | Bad input to a check produces a failure, never a silent pass |

**Rules of thumb.** Check the decision and the trace before the text. Count critical failures on their own. When a check fails, decide whether the agent, the label or the check is wrong.

**Next week.** Week 2 grows these 30 cases into a 100-case dataset with policy versions, risk labels and the authorized customer for each order, then splits it into development and holdout sets. Keep `dataset/cases.jsonl` and `handson/lab.py` unchanged: Week 2 reuses the same case IDs, `case-0001` to `case-0030`.

## References

- [Hands-on file](../handson/week-01-evaluation-basics-handson.md): the lab walkthrough, real output, exercises, drills and solutions for this page.
- [`week-01-evaluation-basics-handson.ipynb`](../handson/week-01-evaluation-basics-handson.ipynb): the same lab as a notebook.
- [Refund policy 2026-01](../../../datasets/policies/refund-policy-2026-01.md): rules R1 to R6, the source of every label.
- [`shared/support_agent.py`](../../../shared/support_agent.py): agent v1 and its five deliberate bugs.
- [Glossary](../../../glossary.md): every term in the course, with the week that introduces it.

---

**Next:** [Week 2 theory: Golden datasets and test design](../../week-02-golden-datasets/theory/week-02-golden-datasets-theory.md) · **Previous:** [Course index](../../../README.md)
