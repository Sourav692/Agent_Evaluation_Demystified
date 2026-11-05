# ADR-002: Tenant fairness through quotas at admission and round robin at dispatch

**Status.** Accepted for the course prototype, 2026-03-20 (SIMULATED date). **Deciders.** Platform team, with the three tenant teams' owners as reviewers. **Context links.** [Theory sections 5, 6 and 9](../theory/week-16-distributed-evaluation-capstone-theory.md#6-fairness-between-teams), [hands-on](week-16-distributed-evaluation-capstone-handson.md), [ADR-001](week-16-distributed-evaluation-capstone-adr-001-lease-queue.md).

## Context

Three teams share four workers. Their workloads differ: the support RAG team submits bursts of retrieval sweeps (40 jobs of 30 s on the simulated day), the refunds team submits release checks that people wait on (12 jobs of 20 s each), and trust and safety submits small safety sweeps (two jobs). Under first-in, first-out dispatch on the simulated day, trust and safety's 30 s job waited a median 470 s and both release decisions took about 500 s against a 300 s target.

We need one team's burst not to starve the others, budgets that hold while work is queued, and a clear answer when the platform will not take more work.

## Decision

1. **Admission in a fixed order.** Role (Week 14's `_authorize`), then budget counting reservations of queued and running jobs, then the team's quota of active jobs, then the queue's capacity. A request is admitted whole or refused whole. Role and budget refusals are final. Quota and capacity refusals say "retry later".
2. **Per-team quotas.** 40 active jobs for support RAG, 30 for refunds, 10 for trust and safety, and 70 for the whole queue. Illustrative values, set from each team's expected peak.
3. **Round robin at dispatch.** A free worker goes to the team whose last lease is oldest among teams with queued jobs, and takes that team's oldest job.

## Options considered

| Option | For | Against |
| --- | --- | --- |
| FIFO | Simple; fair to jobs | The first big submitter holds every worker (trust and safety waited 470 s) |
| Priority classes (release checks first) | Release decisions jump the queue | A team can label everything urgent; low classes can starve; needs governance of who sets priority |
| Dedicated pool per team (silo) | Strong isolation | Idle capacity: trust and safety had two jobs all day |
| Quotas only | Protects admission | Under FIFO the admitted work still runs in arrival order; refuses work that could have run later |
| **Quotas plus round robin** (chosen) | Bounds each team's share of the queue and of the workers | Counts jobs, not seconds; cannot create capacity |

## Consequences

- Under round robin, trust and safety's median wait fell from 470 s to 20 s, and the release decisions from 495 and 530 s to 245 and 340 s. The support team, which caused the burst, absorbed the wait: its p95 rose from 370 s to 510 s.
- v2.3's decision still missed the 300 s SLO. About 1,600 job-seconds arrived in 40 s for four workers, a floor near 400 s. Fairness chooses who waits. Capacity, smaller shards or a smaller sweep quota shortens the wait. Six workers decided v2.3 in 200 s (exercise 1).
- Round robin by job gives the support team's 30 s jobs more worker time than the refunds team's 20 s jobs when both wait. Weighting by expected job duration is the next step if that matters.
- Budgets now count reservations: the refunds team's v2.4 check was refused at t=40 with $0 spent and $0.27 reserved. Without reservations it would have been admitted (exercise 5).
- A quota refusal makes clients resubmit. Content-addressed request IDs make that safe.

## Follow-ups

- Weighted fair sharing by expected seconds, with weights agreed per team.
- A small reserved share for release checks if release SLOs matter more than sweep throughput, decided with the team owners rather than by the platform alone.
- Autoscaling workers on queue depth and age of the oldest job, with the capacity floor as the trigger.
