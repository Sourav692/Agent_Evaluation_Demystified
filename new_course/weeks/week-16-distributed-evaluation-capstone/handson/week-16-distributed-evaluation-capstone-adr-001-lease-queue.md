# ADR-001: A lease-based job queue with at-least-once execution and idempotent completion

**Status.** Accepted for the course prototype, 2026-03-20 (SIMULATED date). **Deciders.** Platform team, with the three tenant teams' owners as reviewers. **Context links.** [Theory sections 3, 4 and 7](../theory/week-16-distributed-evaluation-capstone-theory.md#3-queues-workers-and-leases), [hands-on](week-16-distributed-evaluation-capstone-handson.md), [ADR-002](week-16-distributed-evaluation-capstone-adr-002-tenant-fairness.md).

## Context

Week 14's platform ran every evaluation inside the API call that requested it. Three teams now submit work that takes minutes: retrieval sweeps, release checks of four runs of 30 cases, and fault suites. We need to run that work on a pool of workers, survive a worker dying or stalling, retry failures a bounded number of times, and never lose a shard or charge a team twice. Release decisions read the merged evidence, so a lost or duplicated case changes a verdict.

Constraints:

- A worker can die after doing the work and before reporting it. No dispatch mechanism can tell that worker from one that died before starting.
- Evaluation runs cost money (model calls). Rerunning a job costs real money even when the team is not charged twice.
- Charges, results and job state must agree after any crash.

## Decision

1. **A job table with leases.** A worker leases a job until a deadline (60 s in the prototype, above the longest job). Expired leases go back to the queue without back-off.
2. **A lease token.** Every lease raises the job's token. Completion is a conditional update that matches the caller's token. A worker whose lease was taken over cannot store a result.
3. **One transaction for the effect.** The result and the usage row commit together, keyed by job ID, with a unique index on the usage table's job column as a second guard.
4. **Bounded retries.** A runner failure gets back-off (15 s, then 30 s) and the job is dead-lettered at the third attempt. A dead job leaves its run incomplete, and the merge records it.
5. **Content-addressed IDs.** A job's ID hashes the team, runner, configuration, dataset hash and shard cases. A request's ID hashes its fields. Resends and shared baselines create nothing twice.
6. **SQLite for the prototype.** `BEGIN IMMEDIATE` serialises leases. In production the same tables move to PostgreSQL with `SELECT ... FOR UPDATE SKIP LOCKED`, or dispatch moves to a managed queue with visibility timeouts and the job ledger stays in the database.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| Run in the API call (Week 14) | Simplest; no new parts | A crash loses the run; no limit on concurrent work; long requests hold connections |
| Exactly-once delivery | One execution per job | Cannot be guaranteed when a worker dies after the work and before the ack; systems that offer it deduplicate at the effect anyway |
| At-most-once (no retry) | Never pays twice | Every crash is a lost shard and a HOLD (exercise 3: `max_attempts` 1 turns v2.1's SHIP into HOLD) |
| **At-least-once with idempotent completion** (chosen) | No lost work; one result and one charge per job | Reruns cost real money; needs a lease length tuned to the longest job, or heartbeats |

## Consequences

- On the simulated day, 64 finished jobs had exactly one usage row each and the dead job none. A crash, a stall and a poison job were all recovered or recorded.
- The platform pays for reruns that no team is charged for: $0.0132 of SIMULATED work on the simulated day. The dashboard shows it so it can be budgeted.
- A lease shorter than a job is a failure mode, not a tuning detail: at 15 s every 20 s and 30 s job was dead-lettered (exercise 2). Production workers must renew leases with heartbeats, or job sizes must be capped below the lease.
- The prototype's SQLite queue tops out at roughly 430 to 630 operations per second on one machine with one writer. That is enough to teach the rules, not to run a company's evaluations.
- Shards from workers on other code are refused at merge, because their run ID differs. A rolling deployment produces reruns, not mixed evidence.

## Follow-ups

- Lease renewal (heartbeats) and jitter on back-off.
- Span links for jobs shared between requests, so every request's trace shows its baseline shards.
- Record the worker as a service principal acting on the submitter's behalf in the audit log.
