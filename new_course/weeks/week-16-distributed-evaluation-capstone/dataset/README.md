# Week 16 dataset

Two files configure the queue and script the SIMULATED day. Everything the jobs evaluate is course-root data the earlier weeks already use, read through Week 14's registry. `handson/lab.py` builds a fresh in-memory platform and queue on every run, so these files are the only state.

| File | What it is |
|---|---|
| `queue-policy-v1.json` | The queue's limits: four workers, a 60 s lease, 3 attempts, 15 s back-off (doubled per attempt), a capacity of 70 active jobs, shards of 10 cases, SIMULATED seconds per case per runner, each team's quota, budget and reservation per case, and the two SLOs. Every value is ILLUSTRATIVE, chosen so the day shows each mechanism once |
| `day-script-v1.json` | The SIMULATED day: 16 submissions with their times, and the fault plan (a crash, a stall and a poison shard). Authored for teaching, not recorded from any system |
| `datasets/retrieval/policy-queries-v1.jsonl` | Week 4's 50 policy queries: the support RAG team's sweeps, registered as `support-rag/policy-queries` |
| `datasets/tools/tool-cases-v1.jsonl` | Week 7's 30 tool cases: every release check, registered as `refunds-agent/tool-cases` |
| `datasets/faults/fault-cases-v1.jsonl` | Week 10's 11 fault cases: trust and safety's sweep, registered as `trust-safety/fault-cases` |
| `weeks/week-14-multi-tenant-governance/dataset/tenants-v1.json` | The principals and roles. Week 16 replaces only the budgets and reservations, with the values in `queue-policy-v1.json` |
| `weeks/week-12-release-gates/dataset/release-policy-v1.json` | The release policy: which runs a release check needs, and the gate's rules |

Fields in `queue-policy-v1.json`:

| Field | Meaning |
|---|---|
| `workers` | Worker names. The simulation runs one worker per name |
| `lease_seconds` | How long a lease lasts. Must exceed the longest job (30 s here) |
| `max_attempts` | Attempts before a job is dead-lettered |
| `backoff_seconds` | Wait after the first runner failure, doubled after each later one. Lease expiries get none |
| `capacity` | Most active (queued or leased) jobs across all teams |
| `shard_size` | Cases per job |
| `seconds_per_case` | SIMULATED duration per case, by runner: `retrieval`, `suite:tools`, `suite:faults` |
| `tenants.<id>.max_active_jobs` | The team's quota of active jobs |
| `tenants.<id>.budget_usd` | The team's SIMULATED budget for the day, passed to Week 14's platform |
| `tenants.<id>.reserve_per_case_usd` | The SIMULATED cost reserved per case at admission |
| `slo.release_decision_seconds` | Target from submitting a release check to its decision |
| `slo.queue_wait_p95_seconds` | Target for each team's 95th-percentile wait from enqueue to first lease |

Fields in `day-script-v1.json`:

| Field | Meaning |
|---|---|
| `submissions[].at` | SIMULATED second of the day |
| `submissions[].actor` | The Week 14 principal submitting |
| `submissions[].kind` | `retrieval` (one retriever and k), `release` (candidate against baseline) or `suite` (one agent on one suite and backend) |
| `submissions[].dataset` | The registry name in the actor's tenant |
| `submissions[].note` | Why a submission repeats an earlier one |
| `faults.crash` | The worker that dies, and on which of its leases |
| `faults.pause` | The worker that stalls, on which lease, and for how long |
| `faults.poison` | The tenant and shard index that make every worker raise |

Nothing here is evidence about a real system's capacity, costs or failure rates. The teams and people are fictional, the faults are scripted, and the seconds and dollars are SIMULATED.
