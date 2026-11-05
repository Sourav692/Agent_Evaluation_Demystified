# Week 13 operations runbook: refund agent alerts

The procedure for whoever is paged by the refund agent's online evaluation. It uses the alert names, thresholds and rollback rule in [`dataset/online-policy-v1.json`](../dataset/online-policy-v1.json) and the commands of this week's lab. Every number in it comes from the SIMULATED replay. The concepts are in the [theory file](../theory/week-13-tracing-and-online-evaluation-theory.md), sections 6 to 11.

## Alerts and first moves

| Alert | Severity | Means | First move |
| --- | --- | --- | --- |
| `refund_failure_rate_high` | page | Over 5% of refund attempts failed in the last 6 h, on at least 40 attempts | Check the change log for a deploy in the last 72 h |
| `claim_mismatch` | page | At least one reply in the last 6 h disagrees with the ledger | Open the linked trace and read the ledger read-back line |
| `thumbs_down_rate_high` | ticket | Over 33% thumbs-down in the last 24 h, on at least 40 feedback events | Check `input_drift` and the failure rate for the same hours |
| `input_drift` | ticket | The topic mix moved more than 0.15 from days 1 to 3 | Find the over-represented topic and tell its owner |

## 1. Confirm the alert

1. Read the value and the volume in the alert line, for example `value 0.0588 on 51`: 3 failures in 51 attempts.
2. Check the volume is real traffic, not a test or a replay. In this lab every request is SIMULATED, so note it and carry on.
3. Look at the dashboard row for the window: `handson/runs/week-13/dashboard.html`, regenerated with `lab.py dashboard`.

## 2. Triage from the linked traces

1. Open each linked trace (`runs/week-13/traces/<trace id>.json`, or `lab.py trace <request id>`).
2. Find the ERROR span. Its name says which call failed, and its status message says how, such as `create_refund` with `timeout`.
3. Count the `create_refund` spans. One means the agent did not retry. Two that both failed mean the gateway timed out twice.
4. Read the ledger read-back. A stored refund under a `refund_failed` reply is a claim mismatch: the customer was paid and told otherwise.
5. Read `agent.version` on the root span and compare it with the change log.

## 3. Decide

**A deploy within 72 hours, and `refund_failure_rate_high` firing.** The rollback rule acts after two consecutive firing evaluations. In the replay: deploy of v2.3 at day 9 10:00, fired at 15:00 and 16:00, rolled back to v2.2 at 16:00. If the rule is disabled or has not acted yet, roll back by hand when the traces show the new version failing where the old one retried. Do not wait for a third evaluation to be sure.

**No recent deploy, `claim_mismatch` firing.** Do not roll back: nothing changed. In the replay this is r-1528 (day 4) and r-5116 and r-5159 (day 13), all on v2.2, each with a timeout before the commit followed by one after it.

1. Reconcile: tell each customer the refund was issued, quoting the ledger's refund ID.
2. File the agent defect: after a final timeout, look the refund up by its idempotency key before replying.
3. Check the payment gateway's own health, since two timeouts in a row point at it.

**`thumbs_down_rate_high` or `input_drift`, with the failure rate normal.** Do not roll back. Compare the topic mix with the baseline (`lab.py drift`). During the day-4-to-6 sale, the final-sale share rose from 6% to 40%, denials from about 17% to about 47%, and the failure rate stayed between 0% and 1.0%. Send a ticket to the people who own the sale and the refund policy. The agent applied the policy correctly.

**Failure rate high, no deploy, no mismatches.** Suspect a dependency. Count timeouts by tool in the linked traces, and check whether one gateway or one region carries them.

## 4. Verify

1. After a rollback, confirm the version in the change log and on new root spans (`agent.version`).
2. Wait for the alert to resolve. In the replay `refund_failure_rate_high` resolved at day 9 17:00, one hour after the rollback, once the trailing window held few enough v2.3 failures.
3. Watch the next full window. Days 10 to 12 ran at a 0.0% failure rate on v2.2.
4. Count the customers affected from the traces kept by the tail sampler: every failure and every mismatch is kept. In the replay, 3 customers were told their refund failed while v2.3 served.
5. Add each distinct failure to the offline suite as a case, so the next release is tested against it before it ships.

## 5. What this runbook does not cover

- Paging the payment gateway's owners, or changing the gateway's timeout.
- Alerts on cost or token use: the lab's agents make no model calls.
- Live traffic. These steps have run only against the SIMULATED replay, and the thresholds are illustrative.
