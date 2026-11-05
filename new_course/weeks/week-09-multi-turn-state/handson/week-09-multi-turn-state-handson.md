# Week 9 hands-on: Multi-turn state

Read the [theory](../theory/week-09-multi-turn-state-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  shared/
    session_agent.py                      # session agents v1 and v2, SessionStore, REPLIES templates
    tools.py                              # Week 7's ToolRuntime, strict and lax backends
    refund_store.py                       # the refund ledger
  datasets/
    build_conversations.py                # writes the 25 scenarios
    conversations/conversations-v1.jsonl  # the scenarios
  weeks/week-09-multi-turn-state/
    README.md                             # week index
    theory/week-09-multi-turn-state-theory.md   (and .html)
    handson/
      week-09-multi-turn-state-handson.md     # this file
      week-09-multi-turn-state-handson.ipynb  # the same lab as a notebook
      lab.py                              # harness, five state checks, invariance, wording comparison
      tests/test_lab.py
    dataset/
      README.md                           # fields, provenance, the root files this week reads
      v2-transcripts.jsonl                # v2's replies, frozen, for the exact-text comparison
```

### The notebook

`week-09-multi-turn-state-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library. Checkpoint files go to a temporary directory that is deleted after each run, never into the repository.

### The two agents

Both agents run the same turn logic, `respond` in `shared/session_agent.py`. They differ in where the state lives, what the key is, how a clarification answer is resolved and how the order is found:

```python
class SessionAgentV1:
    def handle(self, customer_id, session_id, message):
        session = self.sessions.setdefault(session_id, {**new_state(), "history": []})   # bugs 1 and 2
        recent = [h for h in session["history"][-HISTORY_WINDOW:] if h]                  # bug 4
        session["order_id"] = recent[-1] if recent else None
        rt = ToolRuntime(self.world, customer_id, store=self.ledger, strict=self.strict)
        reply, outcome = respond(session, message, rt, self.replies, first_candidate)    # bug 3
        ...

class SessionAgentV2:
    def handle(self, customer_id, session_id, message):
        state = self.checkpoints.load(customer_id, session_id) or new_state()
        rt = ToolRuntime(self.world, customer_id, store=self.ledger, strict=self.strict)
        reply, outcome = respond(state, message, rt, self.replies, pick_from_answer)
        state["turns"] += 1
        self.checkpoints.save(customer_id, session_id, state)   # after the tools ran, before replying
        return TurnResult(reply, outcome, state["order_id"], rt.trace)
```

`SessionStore` is one SQLite table with the primary key (customer_id, session_id) and the state as JSON. Every reply comes from the `REPLIES` templates, which lets the lab reword them all at once.

### A scenario

Each line of `conversations-v1.jsonl` is one scenario. conv-08, one turn shown in full:

```json
{"scenario_id": "conv-08", "slice": "clarification",
 "sessions": [{"customer_id": "cust-025", "session_id": "chat-1"}],
 "turns": [{"customer_id": "cust-025", "session_id": "chat-1",
            "message": "The second one.", "restart_before": false,
            "expect": {"outcome": ["refund_offered"], "order_id": "ord-217"}}, ...],
 "expected_refunds": [{"order_id": "ord-217", "amount": 110.0}],
 "expected_escalations": []}
```

The dataset README lists every field.

### The harness and the isolation check

```python
def replay(scenario: dict, agent: str, workdir: Path, strict: bool = True,
           restarts: str = "scenario", replies: dict = REPLIES) -> dict:
    """Run every turn in order. restarts: "scenario" (as written), "none" or "every" turn."""
    ledger = RefundStore(WORLD)
    path = str(workdir / f"{scenario['scenario_id']}-{agent}-{restarts}.sqlite")
    Agent = SESSION_AGENTS[agent]
    bot, built, turns = Agent(WORLD, ledger, path, strict, replies), 1, []
    for i, turn in enumerate(scenario["turns"]):
        restart = {"scenario": turn["restart_before"], "none": False, "every": i > 0}[restarts]
        if restart:
            bot.close()
            bot, built = Agent(WORLD, ledger, path, strict, replies), built + 1
        result = bot.handle(turn["customer_id"], turn["session_id"], turn["message"])
        turns.append({"customer_id": turn["customer_id"], "session_id": turn["session_id"],
                      "message": turn["message"], "restarted": restart, "reply": result.reply,
                      "outcome": result.outcome, "order_id": result.order_id,
                      "calls": [{"name": c.name, "args": c.args, "error": c.error} for c in result.trace]})
    bot.close()
    return {"scenario_id": scenario["scenario_id"], "agent": agent, "agents_built": built, "turns": turns,
            "refunds": [{"order_id": r["order_id"], "amount": r["amount"]} for r in ledger.new_refunds()],
            "escalations": [e["order_id"] for e in ledger.events() if e["action"] == "escalated"]}
```

```python
def check_tenant_isolation(scenario: dict, run: dict) -> CheckResult:
    """No customer sees, or has tools called on, an order they neither own nor mentioned."""
    mentioned = defaultdict(set)
    for i, turn in enumerate(run["turns"], 1):
        me = turn["customer_id"]
        mentioned[me].update(order_ids(turn["message"]))
        touched = order_ids(turn["reply"]) + [c["args"]["order_id"] for c in turn["calls"] if "order_id" in c["args"]]
        for oid in touched:
            order = WORLD["orders"].get(oid)
            if order and order["customer_id"] != me and oid not in mentioned[me]:
                return CheckResult("tenant_isolation", False,
                                   f"turn {i}: {me} was shown or acted on {oid} of {order['customer_id']}", "critical")
    return CheckResult("tenant_isolation", True, "no foreign orders", "critical")
```

The other four checks are `check_outcomes`, `check_order_continuity`, `check_mutation_timing` and `check_ledger`. None reads the reply's wording.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py report --agent v2
```

```text
Session agent v2, strict backend: 25/25 scenarios pass
slice            pass
restart          5/5
clarification    5/5
digression       5/5
isolation        5/5
combined         5/5
Failed checks: outcomes 0, order_continuity 0, mutation_timing 0, ledger 0, tenant_isolation 0
Restarts replayed: 10
```

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py report --agent v1
```

```text
Session agent v1, strict backend: 12/25 scenarios pass
slice            pass
restart          2/5
clarification    3/5
digression       2/5
isolation        2/5
combined         3/5
Failed checks: outcomes 11, order_continuity 12, mutation_timing 0, ledger 11, tenant_isolation 3
  conv-01 (restart): outcomes: turn 2: no_action, expected refund_created
  conv-03 (restart): outcomes: turn 2: no_action, expected refund_offered
  conv-04 (restart): outcomes: turn 3: no_action, expected refund_created
  conv-07 (clarification): outcomes: turn 2: refund_offered, expected escalated_to_human
  conv-08 (clarification): order_continuity: turn 2: order in focus ord-201, expected ord-217
  conv-13 (digression): outcomes: turn 5: clarification_requested, expected refund_created
  conv-14 (digression): outcomes: turn 6: no_action, expected refund_created
  conv-15 (digression): outcomes: turn 8: clarification_requested, expected refund_created
  conv-16 (isolation): outcomes: turn 2: refund_failed, expected no_action
  conv-17 (isolation): outcomes: turn 3: clarification_requested, expected refund_created
  conv-20 (isolation): outcomes: turn 3: refund_failed, expected refund_created
  conv-22 (combined): order_continuity: turn 3: order in focus None, expected ord-211
  conv-25 (combined): outcomes: turn 6: no_action, expected refund_created
Restarts replayed: 10
```

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py show conv-08 --agent v1
```

```text
conv-08 (clarification): Two orders, answered by position: the second. Agent v1.
  1. cust-025/chat-1: Order #201 or #217 arrived broken, I'm not sure which number it was.
     agent: I can see orders #201 and #217. Which one is this about?
     outcome clarification_requested, order in focus None, calls []
  2. cust-025/chat-1: The second one.
     agent: Order #201 (rice cooker, $58.00) can be refunded. Shall I go ahead?
     outcome refund_offered, order in focus ord-201, calls [get_order(ord-201)]
  3. cust-025/chat-1: Yes.
     agent: Done. I've refunded $58.00 for order #201.
     outcome refund_created, order in focus ord-201, calls [get_order(ord-201), create_refund(ord-201)]
  ledger: refunds [{'order_id': 'ord-201', 'amount': 58.0}], escalations []
  PASS outcomes: every turn's outcome is acceptable
  FAIL order_continuity: turn 2: order in focus ord-201, expected ord-217
  PASS mutation_timing: mutations only where expected
  FAIL ledger: unexpected [{'order_id': 'ord-201', 'amount': 58.0}], missing [{'order_id': 'ord-217', 'amount': 110.0}], escalations []
  PASS tenant_isolation: no foreign orders
```

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py show conv-16 --agent v1 --backend lax
```

```text
conv-16 (isolation): Two customers' apps send the same session ID, and the second customer says yes. Agent v1.
  1. cust-001/chat-7: Order #123 arrived damaged.
     agent: Order #123 (ceramic table lamp, $64.00) can be refunded. Shall I go ahead?
     outcome refund_offered, order in focus ord-123, calls [get_order(ord-123)]
  2. cust-025/chat-7: Yes, go ahead.
     agent: Done. I've refunded $64.00 for order #123.
     outcome refund_created, order in focus ord-123, calls [get_order(ord-123), create_refund(ord-123)]
  ledger: refunds [{'order_id': 'ord-123', 'amount': 64.0}], escalations []
  FAIL outcomes: turn 2: refund_created, expected no_action
  FAIL order_continuity: turn 2: order in focus ord-123, expected None
  FAIL mutation_timing: turn 2: create_refund on ord-123
  FAIL ledger: unexpected [{'order_id': 'ord-123', 'amount': 64.0}], missing [], escalations []
  FAIL tenant_isolation: turn 2: cust-025 was shown or acted on ord-123 of cust-001
```

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py invariance --agent v2
python3 weeks/week-09-multi-turn-state/handson/lab.py invariance --agent v1
```

```text
Session agent v2: 25/25 scenarios behave the same with no restarts and with a restart before every turn
Session agent v1: 0/25 scenarios behave the same with no restarts and with a restart before every turn
  conv-01: first differs at turn 2
  conv-02: first differs at turn 3
  conv-03: first differs at turn 2
  conv-04: first differs at turn 2
  conv-05: first differs at turn 2
  conv-06: first differs at turn 3
  conv-07: first differs at turn 2
  conv-08: first differs at turn 2
  conv-09: first differs at turn 3
  conv-10: first differs at turn 3
  conv-11: first differs at turn 2
  conv-12: first differs at turn 2
  conv-13: first differs at turn 2
  conv-14: first differs at turn 2
  conv-15: first differs at turn 2
  conv-16: first differs at turn 2
  conv-17: first differs at turn 3
  conv-18: first differs at turn 3
  conv-19: first differs at turn 3
  conv-20: first differs at turn 3
  conv-21: first differs at turn 3
  conv-22: first differs at turn 2
  conv-23: first differs at turn 2
  conv-24: first differs at turn 3
  conv-25: first differs at turn 2
```

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py wording
```

```text
agent and wording           exact text  state checks
v2, recorded wording            25/25        25/25
v2, reworded                     0/25        25/25
v1, recorded wording            13/25        12/25
```

`lab.py freeze` rewrites `dataset/v2-transcripts.jsonl` from the current v2. Run it only when v2's wording changes on purpose.

Run the tests:

```bash
python3 -m pytest weeks/week-09-multi-turn-state
```

All 13 tests pass. They check the dataset's shape, the two pass counts and v1's failing scenarios, the restart loss, the bound clarification answer, the digression limit, the shared-session leak on both backends, restart invariance, the wording comparison, the harness's refusal of a file without restart flags, and the checkpoint store. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Map each failure to a bug.** For each scenario v1 fails, run `show` and name which of v1's four bugs causes it. Some scenarios have more than one.
2. **Find the digression limit.** The notebook's "your own cases" cell replays 0 to 8 questions between the offer and the yes. At what length does v1 start failing, and why that number?
3. **Turn off the backend's protection.** Run `report --agent v1 --backend lax`. Which scenario now stores a refund it must not, and which checks catch it?
4. **Change the restart schedule.** In the notebook, run `run_suite("v1", restarts="none")` and `run_suite("v1", restarts="every")`. Which scenarios pass only under "every", and why?
5. **Lose a checkpoint save.** In the notebook, replay conv-01's two turns on v2, then put the checkpoint back to its state before the yes, as if the process had died before saving, restart, and say yes again. How many refunds does the ledger hold?
6. **Write a scenario.** Add a conversation where Zara names orders #201, #217 and #260, the agent restarts, and she answers "The last one." Run it on both agents.

### Reading a failed check

Start with the check's name, then the turn number in its reason. `order_continuity` and `outcomes` say which turn went wrong. Run `show` on the scenario, find the first turn whose outcome or order in focus differs from the expectation, and look for a restart marker or a clarification just before it. `tenant_isolation` names the customer and the foreign order: compare the session IDs of the turns around it. `ledger` is the ground truth for money. When it fails alone, the conversation looked right and stored the wrong thing.

## 2. Two debugging drills

### Drill 1: the restart flags went missing

**Break it.** Convert the scenario file with a script that writes `restart` instead of `restart_before`. The notebook's drill cell does this.

**Symptom.** A harness that read the flag with `turn.get("restart_before", False)` would replay no restarts at all. v1 would then pass the restart slice 5/5:

```text
⚠️ With no restarts replayed, v1 passes the restart slice 5/5
❌ validate refuses: conv-01 turn 1 is missing ['restart_before']
```

**Diagnosis.**

1. v1 keeps its state in a dictionary. It cannot survive a restart, so a 5/5 restart slice means the restarts did not happen.
2. The report's last line, `Restarts replayed`, would read 0 instead of 10.
3. The file lost the field. The tolerant read turned a schema change into a silent pass.

**Fix and verify.** `validate` checks every turn for the fields the harness relies on and raises on a missing one, as the second output line shows. Rebuild the file with `datasets/build_conversations.py`, and keep the `Restarts replayed: 10` line in every report. `test_harness_refuses_scenarios_without_restart_flags` pins the refusal.

### Drill 2: the leak fix that keys on the customer alone

**Break it.** A developer fixes conv-16 by keying sessions on the customer ID alone. The notebook's drill cell defines `SessionAgentCustomerKey`, which passes every session as `"any-session"`.

**Symptom.**

```text
⚠️ customer-only key: 24/25
❌ conv-19: turn 3: no_action, expected refund_created
🔧 key (customer, session), as v2 does: 25/25
```

**Diagnosis.**

1. conv-19 is a control: Asha has a refund offer open in her web chat (`web-1`) and an escalation in the app (`app-1`).
2. With the customer-only key, the app turn overwrote the web conversation's state. Her web "Yes, go ahead." finds nothing pending.
3. The isolation scenarios pass. A suite without conv-19 would have shipped the change.

**Fix and verify.** Key by (customer ID, session ID), as v2 does: 25/25. Every key change needs both kinds of case: two customers sharing a session ID, and one customer in two sessions.

## 3. Completion criteria

- [ ] `lab.py report --agent v2` passes 25/25 and `--agent v1` passes 12/25, with 10 restarts replayed.
- [ ] You can name the bug behind each of v1's 13 failures.
- [ ] You can explain why the strict backend's ledger is clean on conv-16 and the isolation check still fails.
- [ ] You can explain the restart-invariance result for both agents without looking at labels.
- [ ] You can state the wording comparison and say what conv-22 shows.
- [ ] `python3 -m pytest weeks/week-09-multi-turn-state` reports 13 passed.

## 4. Solutions

**Exercise 1.** Turning the other three bugs off and keeping one at a time gives this mapping. Bug 1 (memory only): conv-01, 03, 04, 14, 22, 25. Bug 2 (session-ID key): conv-16, 17, 20. Bug 3 (first candidate): conv-07, 08, 25. Bug 4 (three-turn window): conv-13, 14, 15, 25. conv-14 fails from bugs 1 and 4, and conv-25 from bugs 1, 3 and 4.

**Exercise 2.** v1 passes with 0, 1 and 2 questions and fails from 3 on:

```text
🧮 v1: 0:pass 1:pass 2:pass 3:FAIL 4:FAIL 5:FAIL 6:FAIL 7:FAIL 8:FAIL
🧮 v2: 0:pass 1:pass 2:pass 3:pass 4:pass 5:pass 6:pass 7:pass 8:pass
```

v1 searches the orders it looked up in its last 3 turns. The offer turn looked up the order. With 3 questions after it, the offer is 4 turns back when the yes arrives, outside the window.

**Exercise 3.** conv-16. On the lax backend v1's turn for Zara calls `create_refund` on Asha's ord-123, and the ledger stores a $64.00 refund. All five checks fail on it: `outcomes`, `order_continuity`, `mutation_timing` (a refund on a turn that expects none), `ledger` (an unexpected refund) and `tenant_isolation`. The pass count stays at 12/25, because the scenario failed on the strict backend too. Severity changed: a leaked order number became money paid on another customer's order.

**Exercise 4.** With no restarts v1 passes 16: conv-01, 03, 04 and 22 now pass, because only bug 1 broke them. With a restart before every turn it passes 2, conv-07 and conv-16. In conv-07 the restart wipes the open question, so "The damaged one is #174." reads as a fresh message naming one order, and the escalation is right by accident. In conv-16 the restart empties the shared dictionary before Zara's turn, which hides the leak. That is why isolation scenarios must also run without restarts.

**Exercise 5.** One refund. The second yes finds the offer still pending and calls `create_refund` again with the key `cust-001:ord-123:refund`. The backend returns the stored refund with status `existing`, and the agent reports `refund_created`. Without the key, calling `create_refund` twice through Week 7's runtime gives `created` then `existing` on the strict backend (its one-refund-per-order rule) and `created` twice, two refunds, on the lax one. A sketch for the notebook:

```python
with tempfile.TemporaryDirectory() as tmp:
    path, ledger = str(Path(tmp) / "cp.sqlite"), RefundStore(WORLD)
    agent = SessionAgentV2(WORLD, ledger, path)
    agent.handle("cust-001", "web-1", "Order #123 arrived damaged.")
    before = agent.checkpoints.load("cust-001", "web-1")
    agent.handle("cust-001", "web-1", "Yes, go ahead.")
    agent.checkpoints.save("cust-001", "web-1", before)   # the save that was lost
    agent.close()
    again = SessionAgentV2(WORLD, ledger, path).handle("cust-001", "web-1", "Yes, go ahead.")
    print(again.outcome, len(ledger.new_refunds()))      # refund_created 1
```

**Exercise 6.** v2 passes: it reloads the three candidates after the restart and binds "The last one." to ord-260, then refunds $64.00. v1 fails at turn 2 with `no_action`: the restart lost the open question, and "The last one." means nothing to a fresh agent. Expect `clarification_requested` with no order on turn 1, `refund_offered` on ord-260 on turn 2, `refund_created` on turn 3, and one refund of $64.00.

**Design review.** The model answers are in the [theory file's design review](../theory/week-09-multi-turn-state-theory.md#11-design-review).
