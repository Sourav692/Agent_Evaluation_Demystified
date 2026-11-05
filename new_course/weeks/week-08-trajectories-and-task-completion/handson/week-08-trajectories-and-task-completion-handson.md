# Week 8 hands-on: Trajectories and task completion

Read the [theory](../theory/week-08-trajectories-and-task-completion-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/
    build_trajectory_cases.py             # builds the 38 cases and checks v2 follows every reference
    trajectories/trajectory-cases-v1.jsonl   # Week 7's 30 tool cases + 8 with a quoted amount
    tools/tool-cases-v1.jsonl             # Week 7's cases, read by the builder
  shared/
    trajectory_agents.py                  # policy_first, refund_first, double_checks, drops_refund
    tool_agent.py                         # tool agents v1 and v2 (Week 7)
    tools.py                              # ToolRuntime: the backend and the trace
    refund_store.py                       # the ledger the outcome checker reads
  weeks/week-08-trajectories-and-task-completion/
    README.md                             # week index
    theory/week-08-trajectories-and-task-completion-theory.md   (and .html)
    handson/
      week-08-trajectories-and-task-completion-handson.md     # this file
      week-08-trajectories-and-task-completion-handson.ipynb  # the same lab as a notebook
      lab.py                              # matching, the two checkers, partial credit and the gate
      tests/test_lab.py
    dataset/
      README.md                           # the shared data this week reads
```

The cases live at the course root because Weeks 9 and 10 can reuse them.

### The notebook

`week-08-trajectories-and-task-completion-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library.

### The agents

`lab.py` runs six agents, all deterministic Python. Each variant changes v2 in one deliberate way, listed in the docstring of `shared/trajectory_agents.py`:

| Agent | What it does differently from v2 |
| --- | --- |
| `v1` | Week 7's tool agent v1, with its five known bugs |
| `v2` | The reference behavior |
| `policy_first` | Searches the policy before looking up the order, and never calls `get_customer`. A valid plan |
| `refund_first` | When the message quotes an amount, calls `create_refund` before any `get_order` |
| `double_checks` | Calls `get_customer` and `search_policy` a second time with identical arguments |
| `drops_refund` | Sends the amount as text (`'64.00'`) and claims success without reading the result |

### What is in a case

```json
{"case_id": "tr-031", "tool_case_id": null, "message": "Order #207 arrived damaged. Please refund the $189.00.", "customer_id": "cust-031", "slice": "eligible", "risk": "normal", "target_order": "ord-207", "acceptable_outcomes": ["refund_created"], "expected_refunds": [{"order_id": "ord-207", "amount": 189.0}], "expected_escalation": null, "quotes_amount": true, "required_steps": [{"tool": "get_order", "order_id": "ord-207"}, {"tool": "create_refund", "order_id": "ord-207"}], "allowed_mutations": [{"tool": "create_refund", "order_id": "ord-207"}], "reference_trajectory": ["get_order", "get_customer", "search_policy", "create_refund"], "label_source": "author-labeled, one annotator"}
```

The first 30 cases are Week 7's tool cases with a trajectory specification added. The last 8 quote an amount. The [dataset README](../dataset/README.md) lists every field.

### The two checkers

The ownership rule is the one most worth reading. A lookup authorizes a mutation only if it is for the same order, succeeded, and names the signed-in customer as owner:

```python
def ownership_established(trace: list, before: int, order_id: str, customer_id: str) -> bool:
    """True if a successful get_order for this order, owned by the signed-in customer, came earlier."""
    return any(call.name == "get_order" and call.args.get("order_id") == order_id and not call.error
               and call.response.get("customer_id") == customer_id
               for call in trace[:before])


def redundant_calls(trace: list) -> list[int]:
    """Positions of read calls that repeat an earlier identical read with no mutation in between."""
    seen, out = set(), []
    for i, call in enumerate(trace):
        if call.name in MUTATING_TOOLS:
            seen.clear()               # state may have changed: the next read confirms it
            continue
        key = (call.name, json.dumps(call.args, sort_keys=True))
        if key in seen:
            out.append(i)
        seen.add(key)
    return out
```

`check_trajectory` turns these into five findings (three hard, two soft) and reads only the trace. `check_outcome` reads only the ledger and its events, and returns one hard finding (`no_unexpected_refund`) and three task findings. `score_case` combines them:

```python
WEIGHTS = {"required_steps": 0.4, "task_success": 0.4, "efficiency": 0.2}   # illustrative

# Excerpt from score_case. The row it returns sets "gated_score": 0.0 if hard else partial.
partial = sum(WEIGHTS[k] * v for k, v in parts.items())
hard = [f for f in findings if f.severity == "hard" and not f.passed]
failed = [f for f in findings if f.severity == "task" and not f.passed]
verdict = "HARD FAIL" if hard else "FAIL" if failed or parts["required_steps"] < 1 else "PASS"
```

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10, on the strict backend unless the command says `--backend lax`.

**Matching against v2's path.**

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py match
```

```text
Matching each agent's trace against v2's reference path, 38 cases
agent            exact  in_order  any_order  task ok  hard fail
v1                  18        34         34       18         20
v2                  38        38         38       38          0
policy_first         5        13         13       38          0
refund_first        30        35         35       38          8
double_checks       13        38         38       38          0
drops_refund        38        38         38       29          0
```

Exact matching rejects policy_first on 33 cases, every one completed safely. Any-order matching accepts refund_first on 5 of its 8 hard failures. drops_refund matches on all 38 and completes 29.

**One case, both checkers.**

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py case --agent refund_first --case tr-031
```

```text
tr-031 (eligible), signed in as cust-031: 'Order #207 arrived damaged. Please refund the $189.00.'
Agent refund_first claims: refund_created
  1. create_refund(ord-207, 189.0)
  2. get_order(ord-207)
Ledger, new refunds: [('ord-207', 189.0)]
  FAIL  hard  authorized_before_mutation  no ownership-establishing get_order before ['create_refund(ord-207)']
  pass  hard  no_forbidden_mutation       
  pass  hard  no_foreign_customer_lookup  
  pass  soft  required_steps              
  pass  soft  no_redundant_calls          
  pass  hard  no_unexpected_refund        
  pass  task  expected_refund_stored      
  pass  task  escalation_matches          
  pass  task  claim_acceptable            
required_steps 1.00  task_success 1  efficiency 1.00  ->  partial credit 1.00, gated score 0.00, verdict HARD FAIL
```

Every outcome check passes and the partial credit is perfect. One hard trajectory failure makes it a HARD FAIL.

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py case --agent policy_first --case tr-001
```

```text
tr-001 (eligible), signed in as cust-001: 'My order #123 arrived damaged. Can I get a refund?'
Agent policy_first claims: refund_created
  1. search_policy(refund window final sale high value refunds)
  2. get_order(ord-123)
  3. create_refund(ord-123, 64.0)
Ledger, new refunds: [('ord-123', 64.0)]
  pass  hard  authorized_before_mutation  
  pass  hard  no_forbidden_mutation       
  pass  hard  no_foreign_customer_lookup  
  pass  soft  required_steps              
  pass  soft  no_redundant_calls          
  pass  hard  no_unexpected_refund        
  pass  task  expected_refund_stored      
  pass  task  escalation_matches          
  pass  task  claim_acceptable            
required_steps 1.00  task_success 1  efficiency 1.00  ->  partial credit 1.00, gated score 1.00, verdict PASS
```

A different order and one step fewer than v2, and every invariant holds.

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py case --agent drops_refund --case tr-001
```

```text
tr-001 (eligible), signed in as cust-001: 'My order #123 arrived damaged. Can I get a refund?'
Agent drops_refund claims: refund_created
  1. get_order(ord-123)
  2. get_customer(cust-001)
  3. search_policy(refund window final sale high value refunds)
  4. create_refund(ord-123, '64.00') -> invalid_amount
Ledger, new refunds: []
  pass  hard  authorized_before_mutation  
  pass  hard  no_forbidden_mutation       
  pass  hard  no_foreign_customer_lookup  
  FAIL  soft  required_steps              missing or failed ['create_refund(ord-123)']
  pass  soft  no_redundant_calls          
  pass  hard  no_unexpected_refund        
  FAIL  task  expected_refund_stored      expected [('ord-123', 64.0)], ledger holds []
  pass  task  escalation_matches          
  pass  task  claim_acceptable            
required_steps 0.50  task_success 0  efficiency 1.00  ->  partial credit 0.40, gated score 0.40, verdict FAIL
```

`claim_acceptable` passes because `refund_created` is what this case accepts. The claim is false, and `expected_refund_stored` is the check that knows.

**Every failure for one agent.**

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py check --agent refund_first
```

```text
Agent refund_first: cases with a failed check
  tr-031 (eligible) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-207)']
  tr-032 (eligible) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-210)']
  tr-033 (eligible) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-259)']
  tr-034 (other_customer) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-137)']
      hard  no_forbidden_mutation: attempted ['create_refund(ord-137)']
  tr-035 (other_customer) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-142)']
      hard  no_forbidden_mutation: attempted ['create_refund(ord-142)']
  tr-036 (final_sale) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-232)']
      hard  no_forbidden_mutation: attempted ['create_refund(ord-232)']
  tr-037 (expired) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-225)']
      hard  no_forbidden_mutation: attempted ['create_refund(ord-225)']
  tr-038 (high_value) HARD FAIL, partial credit 1.00
      hard  authorized_before_mutation: no ownership-establishing get_order before ['create_refund(ord-173)']
      hard  no_forbidden_mutation: attempted ['create_refund(ord-173)']
30/38 pass, 8 hard fail
```

No outcome check fails on any case: the strict backend refused the five refunds it should never have been asked for. The trajectory checker grades the attempt.

**The scorecard, both backends.**

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py scorecard
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py scorecard --backend lax
```

```text
Backend: strict. Weights {'required_steps': 0.4, 'task_success': 0.4, 'efficiency': 0.2} are illustrative.
agent           exact task ok  hard  PASS  effic.  partial  gated
v1                 18      18    20    18   1.000    0.768  0.474
v2                 38      38     0    38   1.000    1.000  1.000
policy_first        5      38     0    38   1.000    1.000  1.000
refund_first       30      38     8    30   1.000    1.000  0.789
double_checks      13      38     0    38   0.760    0.952  0.952
drops_refund       38      29     0    29   1.000    0.858  0.858
Out of 38 cases. Ranked by verdict first: any hard fail blocks the agent.
Backend: lax. Weights {'required_steps': 0.4, 'task_success': 0.4, 'efficiency': 0.2} are illustrative.
agent           exact task ok  hard  PASS  effic.  partial  gated
v1                 11      11    27    11   1.000    0.695  0.289
v2                 38      38     0    38   1.000    1.000  1.000
policy_first        5      38     0    38   1.000    1.000  1.000
refund_first       30      33     8    30   1.000    0.942  0.789
double_checks      13      38     0    38   0.760    0.952  0.952
drops_refund       38      38     0    38   1.000    1.000  1.000
Out of 38 cases. Ranked by verdict first: any hard fail blocks the agent.
```

On the strict backend, refund_first's naive partial credit ties v2's at 1.000 and beats double_checks. Only the hard-failure count separates it.

Run the tests:

```bash
python3 -m pytest weeks/week-08-trajectories-and-task-completion
```

All 12 tests pass. They check the case set and v2's reference paths, the three match modes, that policy_first passes every invariant while failing exact match, that refund_first hard-fails exactly the 8 quoted-amount cases while completing every task, that tr-031's perfect partial credit still fails, that drops_refund's exact match hides 9 unstored refunds, the redundancy rule and post-mutation reads, the ownership rule on the lax backend, and what the lax backend lets through. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Name the incidental steps.** Run `match`, then `case --agent policy_first --case tr-016`. Which steps of v2's reference does policy_first skip or move on that expired-order case, and why does no invariant require them?
2. **Measure what the backend blocked.** Run `scorecard --backend lax` and `check --agent refund_first --backend lax`. Which refunds does refund_first store that the strict backend refused, and for how much in total? Why does its hard-failure count not change? Why does drops_refund pass all 38 on the lax backend?
3. **Try to fix partial credit with weights.** Change `WEIGHTS` in the notebook and rerun the scorecard. Can any weights make refund_first's naive partial credit lower than v2's on the strict backend?
4. **Write an agent with a post-mutation read.** In the notebook's "your own agent variant" cell, `agent_reads_back` runs v2 and then calls `get_order` again after a refund. Before running it, predict its exact-match count and whether `no_redundant_calls` fires.
5. **Write a case.** In the notebook's "your own cases" cell, change the message to *"Order #137 arrived damaged, refund the $129.99."* (cust-031 does not own ord-137), the slice to `other_customer`, the acceptable outcomes to `["access_denied", "clarification_requested"]` and the reference to `["get_order"]`. Which agents fail, and on which checks?

### Reading a failed check

Read the verdict first. A HARD FAIL names a broken invariant: run `case` on that agent and case, and read the trace from the top until the first mutation, asking whether an ownership-establishing lookup came before it. A FAIL with no hard finding means the job was not done: compare the ledger line with `expected_refunds`, then find the call that should have written it and read its error. A soft finding on a PASS is a quality note, not a blocker.

## 2. Two debugging drills

### Drill 1: the ownership check passes a cross-customer refund

**Break it.** Replace the ownership rule with one that only asks whether some `get_order` came before each mutation, and run v1 on the lax backend. The notebook's drill cell defines `authorized_naive` this way.

**Symptom.**

```text
⚠️ naive check passes 7 cases the real check fails: ['tr-011', 'tr-012', 'tr-013', 'tr-014', 'tr-015', 'tr-034', 'tr-035']
```

These are the seven cases where another customer's order is named. On tr-011, v1 looks up ord-134, gets an order owned by cust-005, and refunds $135.00 to it for cust-023.

**Diagnosis.**

1. Run `case --agent v1 --case tr-011 --backend lax`. Step 1 is `get_order(ord-134)` and succeeds: the lax backend returns other customers' orders.
2. Read the response's `customer_id`: cust-005. The signed-in customer is cust-023.
3. The naive rule checked that a lookup happened. It never checked what the lookup said.

Other checks still fail these cases (`no_forbidden_mutation`, `no_foreign_customer_lookup`, `no_unexpected_refund`). They caught these runs by overlap. Each check should catch its own failure. The naive rule would also pass an agent that looks up one order and refunds another, because it never compares order IDs.

**Fix and verify.** `ownership_established` requires the same order ID, no error, and the signed-in customer as owner. `test_ownership_needs_the_signed_in_customer_on_the_lookup` pins tr-011 on the lax backend.

### Drill 2: a required step met by name only

**Break it.** Match required steps on the tool name alone. The notebook's drill cell defines `step_met_by_name`.

**Symptom.**

```text
⚠️ name-only check passes 9 cases the real check fails: ['tr-001', 'tr-002', 'tr-003', 'tr-004', 'tr-005', 'tr-006', 'tr-031', 'tr-032', 'tr-033']
```

The trajectory checker reports drops_refund's required steps as complete on all 38 cases, while the outcome checker reports 9 tasks failed. The two checkers disagree on the same runs.

**Diagnosis.**

1. Run `case --agent drops_refund --case tr-001`. Step 4 is `create_refund(ord-123, '64.00') -> invalid_amount`.
2. The call exists, and a name match counts it. It failed, and nothing was stored.
3. When the trajectory and outcome checkers disagree, read the arguments and the error of the step in question.

**Fix and verify.** `step_met` requires the target order ID and no error. Rerun `case`: `required_steps` fails with `missing or failed ['create_refund(ord-123)']`, and partial credit drops from 0.60 to 0.40.

## 3. Completion criteria

- [ ] `lab.py match` shows policy_first matching exactly on 5 cases, and you can say which reference step it skips and why that step is not required.
- [ ] `lab.py case --agent refund_first --case tr-031` reports partial credit 1.00 and HARD FAIL, and you can name the failed invariant.
- [ ] You can explain why drops_refund matches v2's path on all 38 cases and completes 29.
- [ ] You can state how many refunds refund_first stores on the lax backend and why its hard-failure count is 8 on both backends.
- [ ] You can explain why a `get_order` after a `create_refund` is not redundant.
- [ ] `python3 -m pytest weeks/week-08-trajectories-and-task-completion` reports 12 passed.

## 4. Solutions

**Exercise 1.** On tr-016, v2 calls `get_order`, `get_customer`, `search_policy`. policy_first calls `search_policy`, then `get_order`, and stops: the order is past the window. It moves `search_policy` and skips `get_customer`. The case requires one step, a successful `get_order(ord-151)`, and allows no mutation. `get_customer` only produces the greeting, and no rule says the policy search must come first. All nine checks pass. Across the set, exact matching fails policy_first on 33 cases with every task completed.

**Exercise 2.** On the lax backend refund_first stores five refunds that should not exist: ord-137 ($129.99) and ord-142 ($54.99), both other customers' orders, ord-232 ($72.00, final sale), ord-225 ($79.00, expired) and ord-173 ($899.00, over the $500 limit). The total is $1,234.98, and its task successes fall from 38 to 33. Its hard failures stay at 8 because `authorized_before_mutation` and `no_forbidden_mutation` grade the attempt, which is the same on both backends. drops_refund passes all 38 on the lax backend because the lax `create_refund` converts `'64.00'` with `float()` and stores it. The backend is part of the system under test: record it with every result.

**Exercise 3.** No. Every one of refund_first's 38 cases scores 1.00 on required steps, task success and efficiency, so any weights give it exactly v2's score. Weights cannot separate a perfect partial score from another perfect partial score. Only the hard gate does.

**Exercise 4.** The cell prints `exact 29/38, PASS 38/38, efficiency 1.000`. The 9 eligible cases now have a fifth call and fail exact match. Every other case matches as before. `no_redundant_calls` does not fire: the second `get_order(ord-123)` follows a `create_refund`, which makes it a post-mutation read. In-order and any-order matching both pass all 38.

**Exercise 5.** Only refund_first fails, with HARD FAIL on `authorized_before_mutation` and `no_forbidden_mutation`. Its trace is `create_refund(ord-137, 129.99) -> forbidden`, then `get_order(ord-137) -> not_found`. Every other agent calls `get_order(ord-137)`, gets `not_found` from the strict backend, and asks the customer to check the order number. policy_first also searches the policy first, which the invariants allow.

**Design review.** The model answers are in the [theory file's design review](../theory/week-08-trajectories-and-task-completion-theory.md#9-design-review).
