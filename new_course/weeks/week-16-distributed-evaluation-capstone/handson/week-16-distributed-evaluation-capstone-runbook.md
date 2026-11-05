# Week 16 operations runbook: the shared evaluation queue

For the people who run the evaluation platform built in Weeks 14 and 16. Every query below runs against the platform's database (`jobs`, `job_events`, `requests`, `usage`, `audit`). Thresholds come from `dataset/queue-policy-v1.json` and are illustrative. For alerts on the refund agent itself in production, use [Week 13's runbook](../../week-13-tracing-and-online-evaluation/handson/week-13-tracing-and-online-evaluation-runbook.md).

## Symptoms and first moves

| Symptom | First check | Section |
| --- | --- | --- |
| A release decision is late (SLO 300 s) | Capacity floor, then per-team waits | 1 |
| Jobs stuck in `leased` | Lease deadlines and worker liveness | 2 |
| A run is UNFINISHED or a release is HOLD | Dead-lettered jobs of the request | 3 |
| A team says it was charged twice | Usage rows per job | 4 |
| A team's submissions are refused | The refusal reason in the audit log | 5 |

## 1. A release decision is late

1. Compute the floor: job-seconds queued or running ahead of the request, divided by live workers. On the simulated day that was about 1,600 job-seconds for 4 workers, about 400 s.
2. If the floor is above the SLO, it is a capacity problem. Add workers, or lower the quota of the team with the large burst (ADR-002). Do not change the dispatch rule.
3. If the floor is well under the SLO, compare per-team p95 waits. One team far above the others under round robin means its jobs are much longer than the others': consider weighting.
4. Record the breach with the request ID, the floor and the action.

## 2. Jobs stuck in `leased`

1. `SELECT job_id, lease_owner, lease_expires, attempts FROM jobs WHERE state='leased'`.
2. A lease past its deadline will be put back on the next `expire_leases`. If none ran, the expirer itself is down: every worker calls it when idle, so check that any worker is alive.
3. Leases expiring on healthy workers (a `retry` event followed by a `stale` event from the same worker) mean the lease is shorter than the job. Raise `lease_seconds` above the longest job, or add lease renewal. Do not lower `max_attempts` to hide it: that turns every slow job into a lost one.

## 3. A run is UNFINISHED or a release is HOLD

1. Find the request's dead jobs: `SELECT job_id, error, attempts FROM jobs WHERE state='dead' AND job_id IN (<request's job_ids>)`.
2. Read the job's history in `job_events`. Three failures with the same error on different workers is a poison job: fix the input or the runner, never retry blindly.
3. A lease-expiry death on every attempt is section 2, not a bad job.
4. After the fix, resubmit. A HOLD on missing evidence has no override (Week 12): only a complete rerun can produce SHIP or BLOCK.

## 4. A team says it was charged twice

1. `SELECT run_id, COUNT(*) FROM usage GROUP BY run_id HAVING COUNT(*) > 1`. The unique index makes this empty for queue jobs. If it is not, the index was dropped: stop dispatch and escalate.
2. Two usage rows under different run IDs for the same work (Drill 1) mean something charged outside `complete`. Find which code path inserts into `usage`.
3. Reruns that were not charged are platform cost, not a double charge. They appear as `stale` events and in the dashboard's wasted-work figure.

## 5. A team's submissions are refused

1. Read the denial in the audit log: `eval.admit` or `eval.run` with decision `deny`, and its reason.
2. `role`: the principal lacks `eval.run`. Route to the team's owner (Week 14).
3. `budget`: the detail shows spent, reserved and requested. Reservations are released as jobs finish. Raising a budget needs the team owner and finance, not the platform team alone.
4. `quota` or `capacity`: the client should resubmit the same request later. Resends are safe because request and job IDs are content hashes.

## Verify after any change

- `python3 -m pytest weeks/week-16-distributed-evaluation-capstone` passes.
- `demo` still shows one usage row per finished job and none per dead job.
- `verify_audit()` on the platform reports no problems, and the anchor stored outside the platform matches the head.

## What this runbook does not cover

Real worker processes, autoscaling, heartbeats, PostgreSQL or a managed queue, object storage for artifacts, and paging. The prototype simulates workers and stores everything on one machine. Every figure it produces is simulated or a prototype measurement.
