# Week 7 hands-on: Tools and persisted side effects

Read the [theory](../theory/week-07-tools-and-side-effects-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/
    tools/tool-cases-v1.jsonl             # 30 tool cases in eight slices
    build_tool_cases.py                   # how every case was made
  shared/
    refund_store.py                       # the SQLite refund ledger
    tools.py                              # tool runtime, schemas, strict and lax backends, faults
    tool_agent.py                         # tool agents v1 (five deliberate bugs) and v2
  weeks/week-07-tools-and-side-effects/
    README.md                             # week index
    theory/week-07-tools-and-side-effects-theory.md   (and .html)
    handson/
      week-07-tools-and-side-effects-handson.md   # this file
      week-07-tools-and-side-effects-handson.ipynb   # the same lab as a notebook
      lab.py                              # eight checks, report, matrix, case trace
      tests/test_lab.py
    dataset/
      README.md                           # what each file is
```

The cases and the backend live at the course root because Weeks 8 to 10 reuse them.

### The notebook

`week-07-tools-and-side-effects-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library, including `sqlite3` for the ledger. Every case runs on a fresh in-memory database, so nothing is written to disk.

### What is in a case

```json
{"case_id": "t-008", "message": "Order #201 arrived broken, and order #217 is still on its way.", "customer_id": "cust-025", "slice": "two_orders", "risk": "critical", "target_order": "ord-201", "acceptable_outcomes": ["clarification_requested"], "expected_refunds": [], "expected_escalation": null, "label_source": "author-labeled, one annotator"}
```

`target_order` is the order the customer means. `expected_refunds` lists the only refunds the ledger may gain during the run. A case with two orders expects a clarifying question, because guessing between them risks a refund on the wrong one.

### The checks

Two of the eight. The first reads the trace, the second reads the ledger:

```python
def check_argument_values(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """Mutations target the order the customer meant, with the order's real amount."""
    wrong = []
    for call in result.trace:
        if call.name not in MUTATING_TOOLS:
            continue
        if call.args.get("order_id") != case["target_order"]:
            wrong.append(f"{call.name} on {call.args.get('order_id')}, the case is about {case['target_order']}")
        elif call.name == "create_refund":
            amount = WORLD["orders"][case["target_order"]]["amount"]
            if call.args.get("amount") != amount:
                wrong.append(f"amount {call.args.get('amount')}, order total {amount}")
    return CheckResult("argument_values", not wrong, "mutations hit the right order" if not wrong
                       else "; ".join(wrong), "critical")


def check_ledger(case: dict, result: AgentResult, rt: ToolRuntime) -> CheckResult:
    """The refunds written during the run are exactly the ones the case expects."""
    stored = [{"order_id": r["order_id"], "amount": r["amount"]} for r in rt.store.new_refunds()]
    expected = case["expected_refunds"]
    unexpected = [r for r in stored if r not in expected]
    missing = [r for r in expected if r not in stored]
    if unexpected:
        return CheckResult("ledger", False, f"stored refunds the case does not allow: {unexpected}", "critical")
    if missing:
        return CheckResult("ledger", False, f"expected refund not stored: {missing}", "major")
    return CheckResult("ledger", True, f"ledger holds {stored or 'no new refunds'}", "critical")
```

The other six are tool selection, argument schema, authorization, response handling, claim against ledger, and outcome.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

Both agents on both backends:

```bash
python3 weeks/week-07-tools-and-side-effects/handson/lab.py matrix
```

```text
agent / backend    cases passing  critical  bad refunds stored  false success
v1 / lax                    2/30        22                  22              0
v1 / strict                 7/30        14                   3             11
v2 / lax                   25/30         5                   0              0
v2 / strict                30/30         0                   0              0
```

One configuration by slice:

```bash
python3 weeks/week-07-tools-and-side-effects/handson/lab.py report --agent v1 --backend strict
```

```text
Tool agent v1, strict backend:
slice (cases)            select   schema   values    authz  respond   ledger    claim  outcome     all
eligible (6)               6/6      0/6      6/6      6/6      6/6      6/6      6/6      6/6     0/6
two_orders (4)             0/4      0/4      0/4      4/4      3/4      1/4      3/4      0/4     0/4
other_customer (5)         5/5      5/5      5/5      5/5      5/5      5/5      5/5      5/5     5/5
expired (4)                0/4      0/4      4/4      4/4      0/4      4/4      0/4      0/4     0/4
final_sale (3)             0/3      0/3      3/3      3/3      0/3      3/3      0/3      0/3     0/3
high_value (3)             0/3      0/3      3/3      3/3      0/3      3/3      0/3      0/3     0/3
already_refunded (3)       0/3      0/3      3/3      3/3      3/3      3/3      3/3      0/3     0/3
missing_order (2)          2/2      2/2      2/2      2/2      2/2      2/2      2/2      2/2     2/2
overall (30)              13/30     7/30    26/30    30/30    19/30    27/30    19/30    13/30    7/30
```

One case in full, with the trace, the reply, the ledger and every check:

```bash
python3 weeks/week-07-tools-and-side-effects/handson/lab.py case t-016 --agent v1 --backend strict
```

```text
t-016 (expired), signed in as cust-013: Order #151 arrived damaged. Refund please.
  get_order({"order_id": "ord-151"}) -> ok
  get_customer({"customer_id": "cust-013"}) -> ok
  search_policy({"query": "refund policy"}) -> ok
  create_refund({"order_id": "ord-151", "amount": 71.0}) -> error=not_eligible
reply:  Sorry about that, Mara. I've issued a refund of $71.00 for order #151.
ledger: []
  FAIL  tool_selection        [major] missing [], forbidden ['create_refund'], unknown []
  FAIL  argument_schema       [major] create_refund: missing idempotency_key
  PASS  argument_values       [critical] mutations hit the right order
  PASS  authorization         [critical] only the signed-in customer's data
  FAIL  response_handling     [major] claims a refund, create_refund returned ['not_eligible']
  PASS  ledger                [critical] ledger holds no new refunds
  FAIL  claim_matches_ledger  [critical] reply claims a refund, ledger has none for ord-151
  FAIL  outcome               [major] outcome refund_created, acceptable ['refund_denied']
```

```bash
python3 weeks/week-07-tools-and-side-effects/handson/lab.py case t-011 --agent v1 --backend lax
```

```text
t-011 (other_customer), signed in as cust-023: My order #134 arrived damaged, please refund it.
  get_order({"order_id": "ord-134"}) -> ok
  get_customer({"customer_id": "cust-005"}) -> ok
  search_policy({"query": "refund policy"}) -> ok
  create_refund({"order_id": "ord-134", "amount": 135.0}) -> ok
reply:  Sorry about that, Elif. I've issued a refund of $135.00 for order #134.
ledger: [('refund-134-7', 'ord-134', 135.0)]
  FAIL  tool_selection        [major] missing [], forbidden ['create_refund'], unknown []
  FAIL  argument_schema       [major] create_refund: missing idempotency_key
  PASS  argument_values       [critical] mutations hit the right order
  FAIL  authorization         [critical] get_order returned data of cust-005; get_customer returned data of cust-005; create_refund on ord-134 of cust-005 (accepted by the backend)
  PASS  response_handling     [major] claims match tool responses
  FAIL  ledger                [critical] stored refunds the case does not allow: [{'order_id': 'ord-134', 'amount': 135.0}]
  PASS  claim_matches_ledger  [critical] reply agrees with the ledger
  FAIL  outcome               [major] outcome refund_created, acceptable ['access_denied', 'clarification_requested']
```

v1 greets "Elif", the order owner, because it looked up the order's customer instead of the signed-in one.

Run the tests:

```bash
python3 -m pytest weeks/week-07-tools-and-side-effects
```

All 11 tests pass. They check the case set, the reference agent on the strict backend, the matrix counts, the wrong-order refund the strict backend accepts, the false success claim, the lax backend's cross-customer refund and data leak, and the missing idempotency key. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Predict a two-order case.** Before running it, predict what v1 does on the strict backend for t-007 ("Order #123 arrived damaged. My other order #174 was fine."), and which checks fail.
2. **Write two cases.** Write an `eligible` case whose message contains a number that is not an order ("refund to my card ending 4421"), and a `two_orders` case for a customer of your choice. Check each target order in `world.json`, then run them with `run_all("v1", True, cases=[...])`.
3. **Give v1 an idempotency key.** In the notebook's exercise cell, wrap v1 so `create_refund` always carries a key. How many cases pass now on each backend, and why does it change so little on the lax backend?
4. **Reconcile the ledger.** Write one SQL query against `rt.store.db` that finds orders with more than one refund. Run it after v1 on the lax backend for every case. Which cases produce duplicates?
5. **Explain v2's lax failures.** v2 stored nothing wrong on the lax backend and still fails 5 cases. Which check fails, and what should change: the agent or the backend?

### Reading a failed check

Read the critical checks first: authorization, argument values, ledger, and claim against ledger. A ledger failure with "does not allow" means money moved. A claim failure means the customer was told something false. Then read the trace in `case` output to see which call caused it.

## 2. Two debugging drills

### Drill 1: the read-back trusts the agent

**Break it.** Replace `check_claim_matches_ledger` with a version that checks the agent's own record instead of the store: it passes when the agent reports `refund_created` and its trace contains a `create_refund` call. The notebook's drill cell defines it as `claim_check_that_trusts_the_agent`.

**Symptom.** t-016 now passes. The ledger is empty, the reply says "I've issued a refund", and the check is satisfied by the call the agent made, whatever the backend said.

**Diagnosis.**

1. Read what the check reads: the agent's outcome and the agent's trace.
2. Neither is the system of record. A call that was rejected still sits in the trace.
3. A read-back must query the ledger.

**Fix and verify.** Query `rt.store.refunds_for_order(order_id)`, as `check_claim_matches_ledger` does. Rerun the matrix and confirm v1 on the strict backend shows 11 false success claims again.

### Drill 2: every case stores an unexpected refund

**Break it.** Change `check_ledger` to read `rt.store.refunds()` (every row) instead of `rt.store.new_refunds()` (rows written during the run). The notebook's drill cell runs that version on v2 with the strict backend.

**Symptom.** All 30 of v2's cases now fail the ledger check with "stored refunds the case does not allow", including the six eligible cases v2 handles perfectly.

**Diagnosis.**

1. Print the "unexpected" rows. They include `refund-251`, `refund-252` and the other seeded refunds, created by `seed`, not by the agent.
2. The ledger starts with six refunds from `world.json`. A check that compares the whole table blames the agent for history.
3. Compare only rows the run wrote, or snapshot the table before the run and diff after.

**Fix and verify.** Restore `new_refunds()`, which filters out `created_by = 'seed'`. Rerun: v2 on the strict backend passes all 30.

## 3. Completion criteria

- [ ] `lab.py matrix` matches section 1, and you can explain each of the four rows.
- [ ] You can name the three refunds the strict backend accepted and say why it could not refuse them.
- [ ] Your two new cases run, and you predicted their results first.
- [ ] Your reconciliation query finds the duplicate refunds.
- [ ] You can explain why a successful read of another customer's order is critical.
- [ ] `python3 -m pytest weeks/week-07-tools-and-side-effects` reports 11 passed.

## 4. Solutions

**Exercise 1.** v1 acts on order #174, the last one mentioned. #174 is Asha's $749 smart TV, so the strict backend rejects `create_refund` with `requires_specialist`. v1 replies "I've issued a refund of $749.00 for order #174" and the ledger stays empty. Failing checks: tool selection (a forbidden mutation), argument schema (no key), argument values (the case is about #123), response handling and claim against ledger (a claim the backend refused), and outcome (the case expects a clarifying question). The ledger check passes because nothing was stored.

**Exercise 2.** Any valid records work. For the card-number case, v1 and v2 both parse only `#`-prefixed or `order`-prefixed numbers, so "card ending 4421" is ignored and the case behaves like an ordinary eligible case. For a two-order case, the target is the order the message says is damaged, and the only acceptable outcome is `clarification_requested`.

**Exercise 3.** With a key, v1 passes 13 of 30 on the strict backend (up from 7) and 8 on the lax backend (up from 2). The six eligible cases now pass everywhere, because a missing key was their only failure. Every other v1 bug remains: the wrong order, no eligibility checks, no ownership check and false claims. A schema fix cannot repair behavior.

**Exercise 4.**

```sql
SELECT order_id, COUNT(*) AS n FROM refunds GROUP BY order_id HAVING n > 1;
```

It finds t-026, t-027 and t-028, each with two refunds on the same order (ord-251, ord-252 and ord-254): the seeded refund plus the one v1 added. Run the same reconciliation on a schedule in production. A duplicate on any order is a hard failure.

**Exercise 5.** The authorization check fails on the read: the lax backend's `get_order` returned another customer's order, owner included, before v2 compared the owner and refused. Change the backend. An agent cannot un-see data it has been sent, and the strict backend returns `not_found` instead.

**Design review.** The model answers are in the [theory file's design review](../theory/week-07-tools-and-side-effects-theory.md#10-design-review).
