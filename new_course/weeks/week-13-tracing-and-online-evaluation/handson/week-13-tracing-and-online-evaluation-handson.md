# Week 13 hands-on: Tracing and online evaluation

Read the [theory](../theory/week-13-tracing-and-online-evaluation-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions. The on-call procedure is in the [operations runbook](week-13-tracing-and-online-evaluation-runbook.md).

## 1. Lab

### Files

```text
new_course/
  shared/
    tracing.py                            # span recorder, TracedRuntime, trace_request, head sampling, redaction
    fault_agents.py                       # Week 10's stable_key and no_retry agents: versions v2.2 and v2.3
    tools.py                              # Week 7's runtime: faults=, chunks=
    refund_store.py                       # Week 7's SQLite ledger, read back after every request
  requirements-integrations.txt           # optional opentelemetry-sdk pin, for the otel command only
  weeks/week-13-tracing-and-online-evaluation/
    README.md                             # week index
    theory/week-13-tracing-and-online-evaluation-theory.md   (and .html)
    handson/
      week-13-tracing-and-online-evaluation-handson.md      # this file
      week-13-tracing-and-online-evaluation-handson.ipynb   # the same lab as a notebook
      week-13-tracing-and-online-evaluation-runbook.md      # what to do when an alert fires
      lab.py                              # traffic, trace, replay, sampling, drift, redaction, dashboard, otel
      tests/test_lab.py
      runs/week-13/                       # written by the dashboard command, git-ignored
    dataset/
      README.md                           # the two files below and the shared data this week reads
      traffic-config-v1.json              # SIMULATED traffic: volume, topic mix, faults, feedback, versions, deploy
      online-policy-v1.json               # alerts, rollback rule, sampling, redaction salt
```

### The notebook

`week-13-tracing-and-online-evaluation-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab and `shared/tracing.py` use only the standard library. The `otel` command and the notebook's last optional cell also need `opentelemetry-sdk==1.45.2` from `requirements-integrations.txt`. It is free to run and calls no service.

Every request is SIMULATED. `build_traffic` generates 5,600 of them from the seed in `traffic-config-v1.json`, and `replay` serves them against `datasets/world.json`, one fresh in-memory ledger per request. Span durations are fixed costs from `shared/tracing.LATENCY_MS`, not measurements. The agents are Week 10's deterministic code standing in for a model.

### The two versions and the traffic

| Version | Agent in `shared/fault_agents.py` | On a `create_refund` timeout |
| --- | --- | --- |
| v2.2, serving from day 1 | `stable_key` | retries once with the same idempotency key |
| v2.3, deployed day 9 at 10:00 | `no_retry` | tells the customer the refund failed |

The configuration fixes the rest:

- **Volume.** 400 requests a day for 14 days, at random times.
- **Topics.** Seven message templates, each matched to an order its policy outcome suits: a damaged eligible order, a late opening, a clearance-sale item, a high-value item, an already refunded order, no order number, and someone else's order. Days 4 to 6 are a clearance sale with far more final-sale requests.
- **Personal data.** 30% of messages start with the customer's name and a synthetic email, and 5% end with a published test card number.
- **Gateway faults.** Every `create_refund` call times out with probability 8%, half before the commit and half after.
- **Feedback.** 30% of requests get a SIMULATED thumbs-up or thumbs-down, with a thumbs-down probability that depends on the outcome.

### Instrumenting the runtime

`TracedRuntime` subclasses Week 7's runtime and changes nothing it does. It wraps every call in a TOOL span and advances the simulated clock:

```python
@dataclass
class TracedRuntime(ToolRuntime):
    """The Week 7 runtime, unchanged, with a TOOL span around every call."""

    tracer: Tracer | None = None

    def call(self, name: str, **args):
        attrs = {TOOL_NAME: name, TOOL_PARAMETERS: json.dumps(args, sort_keys=True)}
        with self.tracer.span(name, "TOOL", attrs) as span:
            record = super().call(name, **args)
            self.tracer.clock.advance(LATENCY_MS["timeout"] if record.error == "timeout" else LATENCY_MS.get(name, 50))
            span.attributes[OUTPUT_VALUE] = json.dumps(record.response, sort_keys=True, default=str)
            span.status, span.status_message = ("ERROR", record.error) if record.error else ("OK", "")
        return record
```

Its `_tool_search_policy` opens a RETRIEVER span inside the TOOL span and lists each chunk as `retrieval.documents.N.document.id` and `.document.content`. `trace_request` opens the AGENT root span, runs the agent and adds the LLM span for the reply step. The current span lives in a context variable, so a TOOL span finds its parent without being passed one.

### The online checks

The checks read the spans and the ledger, never an expected outcome:

```python
def online_checks(row: dict) -> dict:
    """Reference-free checks: no expected outcome, only the trace and the ledger read-back."""
    spans = row["spans"]
    creates = [s for s in spans if s.name == "create_refund"]
    stored = [r for r in row["ledger"] if r["order_id"] == row["order_id"]]
    return {
        "refund_attempt": bool(creates),
        "refund_failure": bool(creates) and creates[-1].status == "ERROR",
        "claim_mismatch": (row["outcome"] == "refund_created") != bool(stored),
        "tool_errors": [f"{s.name}:{s.status_message}" for s in spans if s.kind == "TOOL" and s.status == "ERROR"],
        "root_error": spans[0].status == "ERROR",
    }
```

`replay` serves the traffic hour by hour. At the end of each hour it computes every alert's metric over its trailing window from `online-policy-v1.json`, opens or resolves alert events, and applies the rollback rule:

```json
"rollback": {"alert": "refund_failure_rate_high", "consecutive_evaluations": 2, "max_hours_since_deploy": 72}
```

A rollback decided at an evaluation applies to the next hour's traffic. Event times are evaluation times, so "fired day 9 15:00" means the evaluation at the end of the 14:00 hour.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

**The traffic:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py traffic
```

```text
5600 SIMULATED requests over 14 days (traffic-v1, seed 13)
  days 1-3                   damaged 42%  late 11%  final_sale 6%  high_value 8%  already_refunded 7%  no_order_number 17%  other_customer 9%
  days 4-6 (clearance sale)  damaged 25%  late 8%  final_sale 40%  high_value 5%  already_refunded 4%  no_order_number 11%  other_customer 7%
  days 7-14                  damaged 39%  late 12%  final_sale 5%  high_value 8%  already_refunded 7%  no_order_number 19%  other_customer 10%
  first create_refund attempt would time out: 459 requests (8.2%)
  r-0001 day 1 cust-001: My order #123 arrived damaged. Can I get a refund?
  r-0002 day 1 cust-029: Checking on the refund for order #253, it arrived damaged.
  r-0003 day 1 cust-028: Checking on the refund for order #252, it arrived damaged.
```

Every request draws its gateway faults, and they matter only when the agent calls `create_refund`.

**One trace, as exported:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py trace r-3211
```

```text
r-3211 (as exported, redacted), version v2.2, trace 2ed02ab02c75a2f26396d78aa12208ec
  support_request     AGENT       6010 ms  OK                        Hi, this is <name> (<email>). My order #218 arrived damaged. Can I get a refund?
    get_order         TOOL          40 ms  OK                        {"order_id": "ord-218"}
    search_policy     TOOL         120 ms  OK                        {"query": "refund window final sale high value refunds"}
      retrieve        RETRIEVER     90 ms  OK                        ['refund-policy-2026-01#R3', 'refund-policy-2026-01#R2', 'refund-policy-2026-01#R4']
    create_refund     TOOL        5000 ms  ERROR (timeout)           {"amount": 28.0, "idempotency_key": "user-037c9b94f2:ord-218:refund", "order_id": "ord-218"}
    create_refund     TOOL         250 ms  OK                        {"amount": 28.0, "idempotency_key": "user-037c9b94f2:ord-218:refund", "order_id": "ord-218"}
    compose_reply     LLM          600 ms  OK                        I've issued a refund of $28.00 for order #218.
  ledger read-back: [('refund-218-7', 'ord-218')]
  online checks: {'refund_attempt': True, 'refund_failure': False, 'claim_mismatch': False, 'tool_errors': ['create_refund:timeout'], 'root_error': False}, feedback: None
```

Indentation is the parent link. The first `create_refund` timed out before the commit and the retry stored `refund-218-7`. The name, the email and the customer ID inside the idempotency key are redacted. Add `--raw` to see the in-process spans before redaction.

**The same failure on v2.3:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py trace r-3372
```

```text
r-3372 (as exported, redacted), version v2.3, trace 70e685b60d68c978f253262400231fa2
  support_request     AGENT       5760 ms  ERROR (refund_failed)     My order #132 arrived damaged. Can I get a refund?
    get_order         TOOL          40 ms  OK                        {"order_id": "ord-132"}
    search_policy     TOOL         120 ms  OK                        {"query": "refund window final sale high value refunds"}
      retrieve        RETRIEVER     90 ms  OK                        ['refund-policy-2026-01#R3', 'refund-policy-2026-01#R2', 'refund-policy-2026-01#R4']
    create_refund     TOOL        5000 ms  ERROR (timeout)           {"amount": 42.5, "idempotency_key": "user-1fda4fe0c8:ord-132:refund", "order_id": "ord-132"}
    compose_reply     LLM          600 ms  OK                        I couldn't issue the refund (timeout). Please try again later.
  ledger read-back: []
  online checks: {'refund_attempt': True, 'refund_failure': True, 'claim_mismatch': False, 'tool_errors': ['create_refund:timeout'], 'root_error': True}, feedback: down
```

**Fourteen days, with the rollback rule:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay
```

```text
Replay of SIMULATED traffic, automatic rollback on
 day  version    requests refund attempts failure rate mismatches thumbs-down  drift  p95 ms
   1  v2.2            400             173         0.0%          0         26%   0.04    1010
   2  v2.2            400             178         0.0%          0         26%   0.05    1010
   3  v2.2            400             150         0.0%          0         29%   0.07    1010
   4  v2.2            400             104         1.0%          1         39%   0.34    1010
   5  v2.2            400             104         0.0%          0         34%   0.33    1010
   6  v2.2            400              96         0.0%          0         34%   0.34    1010
   7  v2.2            400             154         0.0%          0         27%   0.05    1010
   8  v2.2            400             143         0.0%          0         23%   0.09    1010
   9  v2.2/v2.3       400             148         2.7%          0         22%   0.07    1010
  10  v2.2            400             174         0.0%          0         27%   0.05    1010
  11  v2.2            400             159         0.0%          0         23%   0.06    1010
  12  v2.2            400             158         0.0%          0         24%   0.04    1010
  13  v2.2            400             148         1.4%          2         25%   0.09    1010
  14  v2.2            400             158         0.6%          0         22%   0.05    1010
Changes:
  day 9 10:00  deploy           v2.2 -> v2.3
  day 9 16:00  rollback decided refund_failure_rate_high firing for 2 evaluations
  day 9 16:00  rollback         v2.3 -> v2.2
Alerts:
  input_drift              ticket  fired day 4 07:00, value 0.154 on 403, resolved day 7 14:00
  thumbs_down_rate_high    ticket  fired day 4 12:00, value 0.361 on 108, resolved day 5 18:00
  claim_mismatch           page    fired day 4 20:00, value 1 on 104, resolved day 5 02:00
  thumbs_down_rate_high    ticket  fired day 5 19:00, value 0.342 on 114, resolved day 7 02:00
  thumbs_down_rate_high    ticket  fired day 7 03:00, value 0.333 on 132, resolved day 7 05:00
  thumbs_down_rate_high    ticket  fired day 7 06:00, value 0.331 on 127, resolved day 7 07:00
  refund_failure_rate_high page    fired day 9 15:00, value 0.0588 on 51, resolved day 9 17:00
  claim_mismatch           page    fired day 13 19:00, value 1 on 96, resolved day 14 04:00
Incident: deploy at day 9 10:00, detected after 5 h, rolled back after 6 h; 113 requests on the bad version, 3 refund failures, 0 claim mismatches
```

Read the columns against each other. Days 4 to 6 move drift and thumbs-down and leave the failure rate near zero. Day 9 moves the failure rate and leaves the other two where they were. The p95 latency never moves: fewer than 5% of requests meet a timeout. The value after "on" is the alert's volume: refund attempts, requests or feedback events in the window.

**The same traffic without the rule** (shortened here: the alert list has 26 events, 20 of them pages after the deploy):

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay --no-rollback
```

```text
Replay of SIMULATED traffic, automatic rollback off
 day  version    requests refund attempts failure rate mismatches thumbs-down  drift  p95 ms
   ...
   9  v2.2/v2.3       400             148         6.1%          4         24%   0.07    1010
  10  v2.3            400             174         5.7%          6         30%   0.05    1010
  11  v2.3            400             159         5.7%          7         25%   0.06    1010
  12  v2.3            400             158         5.7%          4         28%   0.04    1010
  13  v2.3            400             148         8.1%          5         27%   0.09    1010
  14  v2.3            400             158         9.5%          5         24%   0.05    1010
Changes:
  day 9 10:00  deploy           v2.2 -> v2.3
Alerts:
  ...
  refund_failure_rate_high page    fired day 9 15:00, value 0.0588 on 51, resolved day 9 19:00
  claim_mismatch           page    fired day 9 17:00, value 1 on 101, resolved day 10 18:00
  refund_failure_rate_high page    fired day 9 22:00, value 0.125 on 40, resolved day 9 23:00
  ...
Incident: deploy at day 9 10:00, detected after 5 h, never rolled back; 2229 requests on the bad version, 64 refund failures, 31 claim mismatches
```

The bad version's failure rate hovers near the 5% threshold. The alert fires and resolves over and over, and the thumbs-down rate stays inside the range of days 1 to 8.

**The trace behind the day-4 page:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py trace r-1528
```

```text
r-1528 (as exported, redacted), version v2.2, trace c1c72101a95a0a9f6eabf2a52018a468
  support_request     AGENT      10760 ms  ERROR (refund_failed)     My order #210 arrived damaged. Can I get a refund?
    get_order         TOOL          40 ms  OK                        {"order_id": "ord-210"}
    search_policy     TOOL         120 ms  OK                        {"query": "refund window final sale high value refunds"}
      retrieve        RETRIEVER     90 ms  OK                        ['refund-policy-2026-01#R3', 'refund-policy-2026-01#R2', 'refund-policy-2026-01#R4']
    create_refund     TOOL        5000 ms  ERROR (timeout)           {"amount": 59.0, "idempotency_key": "user-bea65b480c:ord-210:refund", "order_id": "ord-210"}
    create_refund     TOOL        5000 ms  ERROR (timeout)           {"amount": 59.0, "idempotency_key": "user-bea65b480c:ord-210:refund", "order_id": "ord-210"}
    compose_reply     LLM          600 ms  OK                        I couldn't issue the refund (timeout). Please try again later.
  ledger read-back: [('refund-210-7', 'ord-210')]
  online checks: {'refund_attempt': True, 'refund_failure': True, 'claim_mismatch': True, 'tool_errors': ['create_refund:timeout', 'create_refund:timeout'], 'root_error': True}, feedback: None
```

**Sampling:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py sampling
```

```text
sampler           traces kept spans kept   failure traces kept
head 1%                    71        338   0 of 8
head 5%                   299       1465   0 of 8
head 10%                  589       2869   1 of 8
tail + head 5%            898       4465   8 of 8
refund_failure_rate_high computed from a 5% head sample: fires in 0 hours, first never
refund_failure_rate_high computed from a 10% head sample: fires in 0 hours, first never
```

**Input drift against quality:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py drift
```

```text
Input drift (topic mix vs days 1-3) against quality signals, per day
 day  drift sale share  denied thumbs-down failure rate
   1   0.04         5%     17%         26%         0.0%
   2   0.05         6%     16%         26%         0.0%
   3   0.07         7%     19%         29%         0.0%
   4   0.34        40%     47%         39%         1.0%
   5   0.33        39%     46%         34%         0.0%
   6   0.34        40%     48%         34%         0.0%
   7   0.05         5%     17%         27%         0.0%
   8   0.09         4%     19%         23%         0.0%
   9   0.07         5%     17%         22%         2.7%
  10   0.05         5%     16%         27%         0.0%
  11   0.06         5%     18%         23%         0.0%
  12   0.04         7%     17%         24%         0.0%
  13   0.09         4%     18%         25%         1.4%
  14   0.05         6%     16%         22%         0.6%
```

**Redaction:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py redaction
```

```text
5600 traces; 1619 messages carry a name and email, 289 a card number
export                      emails  card numbers  customer IDs  names
patterns only                    0             0             0   1619
patterns + session names         0             0             0      0
```

**The dashboard:**

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py dashboard
```

```text
wrote weeks/week-13-tracing-and-online-evaluation/handson/runs/week-13/dashboard.html and 20 linked traces
```

Open the file in a browser. Windows with an alert firing are shaded, and each alert links to up to three exported traces in `runs/week-13/traces/`.

**Optional: the real OpenTelemetry SDK.** Free, no service, no key. Checked on 2026-11-05 in an isolated environment:

```bash
uv run --isolated --no-project --python 3.12 --with opentelemetry-sdk==1.45.2 \
    python weeks/week-13-tracing-and-online-evaluation/handson/lab.py otel
```

```text
OpenTelemetry SDK received 226 redacted spans from the first 50 requests; spans that differ from ours: none
{"name": "support_request", "context": {"trace_id": "0xe8d79f49af6d114c4a6f188a424e617b", "span_id": "0xcd502d42af1ffe0d", "trace_state": "[]"}, "kind": "SpanKind.INTERNAL", "parent_id": null, "start_time": "2026-03-01T00:01:11.594000Z", "end_time": "2026-03-01T00:01:12.604000Z", "status": {"status_code": "OK"}, "attributes": {"openinference.span.kind": "AGENT", "input.value": "My order #123 arrived damaged. Can I get a refund?", "session.id": "s-0001", "user.id": "user-5fa7a62ee4", "agent.version": "v2.2", "output.value": "I've issued a refund of $64.00 for order #123.", "refund.outcome_claimed": "refund_created", "refund.order_id": "ord-123"}, "events": [], "links": [], "resource": {"attri
```

`otel_export` hands the SDK our trace and span IDs through a custom ID generator, and places simulated day 1 00:00 at 2026-03-01 UTC. Without the SDK the command exits with `opentelemetry-sdk is not installed; see requirements-integrations.txt`. Sending the spans to a collector instead of memory means swapping the in-memory exporter for an OTLP exporter, which this course has not run.

Run the tests:

```bash
python3 -m pytest weeks/week-13-tracing-and-online-evaluation
```

All 13 tests pass. They pin the W3C ID formats and a `traceparent` round trip, the span tree of r-3211, reproducible traffic and trace IDs, the three online checks on r-3211, r-3372 and r-1528, the deploy's detection and rollback against the counterfactual, the absence of refund pages before the deploy, the sampling numbers, redaction across every exported span, and the dashboard's trace links. The OpenTelemetry test runs the SDK round trip when the SDK is installed and passes on the missing-SDK path otherwise. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Read two traces.** Run `trace r-3211` and `trace r-3372`. For each, name the span that failed, the root span's status, and what the ledger holds. Which field of the trace would a support agent read first, and which check would you trust?
2. **Predict the sampler.** Before running `sampling`, predict how many of the 8 failure traces a 50% head sampler keeps. Then add `0.5` to the rates in `sampling_report` in the notebook and run it. Compare its cost with the tail sampler's.
3. **Tune the alert.** In the notebook's "your own alert" cell, try a 4% threshold with a minimum of 30 attempts, then a 12-hour window. For each, record the first firing after the deploy and the number of evaluations that fire on windows only v2.2 served.
4. **Page or rollback.** The `claim_mismatch` page fires on day 13 at 19:00. Find the requests behind it with the dashboard's links or with `trace`, and decide what to do. Use the runbook.
5. **Feedback as a trigger.** Suppose the rollback rule watched `thumbs_down_rate_high` instead. Using the `replay` output, say when it would have acted and what it would have rolled back.

### Reading a failed check

Start from the alert, not the trace. Read the alert's value and volume, then the change log: a deploy within the rule's 72 hours points at the new version. Open the linked traces and find the ERROR span: its name and status message say which call failed. Then read the ledger read-back line. A refund stored under a failure claim is a claim mismatch, the customer's money moved and nobody told them. For a drift or feedback alert, compare the topic mix and the failure rate on the same days before touching the agent.

## 2. Two debugging drills

### Drill 1: the alert that paged on one failure

**Break it.** To page sooner, someone sets `refund_failure_rate_high` to a 1-hour window with no minimum volume. The notebook's drill cell evaluates that rule against the replay.

**Symptom.** The rule fires at 8 evaluations, and 5 of them cover only v2.2 traffic: day 4 20:00, day 9 22:00, day 13 19:00, day 13 22:00 and day 14 10:00. On-call is paged five times for a version that is working.

**Diagnosis.**

1. Print each firing evaluation's volume. Most hours hold 3 to 10 refund attempts, and the five false pages had 5 to 10. One failure among them is 10% to 20%, far over 5%.
2. Compare with the baseline. v2.2 fails about 1 attempt in 300, which over 14 days is a handful of single failures, each enough to page under this rule.
3. Check what it gained. It fires first at day 9 11:00, four hours earlier than the policy rule, on 1 failure in 12 attempts. That page looks exactly like the false ones.

**Fix and verify.** Restore the 6-hour window and the minimum of 40 attempts. `alert_hours(run, base)` then fires at 2 evaluations, day 9 15:00 and 16:00, and none on v2.2-only windows. `test_no_refund_page_before_the_deploy_and_drift_alerts_only_around_the_sale` pins the result.

### Drill 2: the export that leaked names

**Symptom.** An exporter that redacts by pattern passes a leak check for emails, card numbers and customer IDs. The notebook's drill cell shows r-3211's exported root span still reading `Hi, this is Arjun Mehta (<email>).`, and `leaks` reports `name: 1`.

**Diagnosis.**

1. Run `redaction`: patterns alone leave 1,619 names, one in every message that carries an identity.
2. Look at what the patterns match. Emails and card numbers have a fixed shape. Names do not, and no regular expression separates "Arjun Mehta" from "Order Number".
3. Find who knows the name. The runtime already holds the signed-in customer's record, so the exporter can mask that customer's full, first and last name.

**Fix and verify.** Export with `identity_aware=True`, the default in `export_trace`. The root span reads `Hi, this is <name> (<email>).`, `redaction` reports 0 names, and `test_export_redacts_names_emails_card_numbers_and_customer_ids` checks every exported span against all 40 customer names and their emails.

## 3. Completion criteria

- [ ] `lab.py trace r-3211` shows one AGENT root, five children, a RETRIEVER under `search_policy`, and the timed-out `create_refund` as the only ERROR span.
- [ ] You can explain why r-1528 is a claim mismatch and r-3372 is not.
- [ ] `lab.py replay` shows the deploy detected after 5 hours and rolled back after 6, and you can read the day-9 evaluation table in the theory file's section 7.1.
- [ ] You can say why the alert needs a minimum volume, with the numbers from Drill 1.
- [ ] `lab.py sampling` shows 0 of 8 failure traces at 5% head sampling and 8 of 8 with tail sampling, and you can explain why alerts must count every request.
- [ ] You can explain from `lab.py drift` why the sale is input drift and the deploy is not.
- [ ] `lab.py redaction` shows 0 names after identity-aware redaction.
- [ ] You can follow the runbook from an alert to a verified rollback.
- [ ] `python3 -m pytest weeks/week-13-tracing-and-online-evaluation` reports 13 passed.

## 4. Solutions

**Exercise 1.** In r-3211 the first `create_refund` span is ERROR (timeout), the root span is OK, and the ledger holds `refund-218-7`. In r-3372 the only `create_refund` is ERROR (timeout), the root span is ERROR (`refund_failed`) and the ledger is empty. A support agent reads the root span's input and output first, the customer's words and the reply. Trust the ledger read-back: in r-1528 the reply says the refund failed and the ledger holds it.

**Exercise 2.** A 50% head sampler keeps 2,772 traces, 13,332 spans, and 2 of the 8 failure traces. A fair coin would keep 4 on average, and with 8 traces 2 is an ordinary result. The tail sampler stores about a third as many traces (898) and keeps all 8. Head sampling keeps failures in proportion to the rate at best. Only a decision made after the trace ends can keep all of them.

**Exercise 3.** At 4% with a minimum of 30 attempts, the alert first fires at day 9 13:00, two hours sooner. It fires at 9 evaluations, and 3 of them cover only v2.2 traffic: day 13 22:00, day 13 23:00 and day 14 00:00. The 12-hour window never fires in this run: v2.3 served for only 6 hours, too little to lift a 12-hour rate over 5%. Faster detection costs false pages, and a longer window misses short incidents.

**Exercise 4.** The page stays open from day 13 19:00 to day 14 04:00 and covers r-5116 (day 13 18:00) and r-5159 (day 13 21:00). Both traces show two `create_refund` timeouts, the first before and the second after the commit, and both ledgers hold a refund the customer was told failed. Only v2.2 served and no deploy happened within 72 hours, so the rule correctly does not roll back. Follow the runbook's reconcile branch: tell both customers the refund was issued, and file the agent fix of looking the refund up by its idempotency key after a final timeout.

**Exercise 5.** `thumbs_down_rate_high` fired on day 4 at 12:00 and again on days 5 and 7, all during the sale or the day after it, when nothing had been deployed. A rule keyed to it would have no deploy to roll back. With no deploy-recency condition it would roll back a working version. It never fired on day 9: the thumbs-down rate that day was 22%, lower than on any earlier day. Feedback found the sale, not the incident.

**Design review.** The model answers are in the [theory file's design review](../theory/week-13-tracing-and-online-evaluation-theory.md#13-design-review).
