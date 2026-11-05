# Week 16 hands-on: Distributed evaluation capstone

Read the [theory](../theory/week-16-distributed-evaluation-capstone-theory.md) first. This file holds the lab, the capstone checklist, the demo script, the debugging drills, the completion checklist and the solutions. The two architecture decision records and the runbook are beside it.

## 1. Lab

### Files

```text
new_course/
  shared/
    governance.py                         # Week 14's platform: principals, _authorize, registry, audit, usage
    tracing.py                            # Week 13's tracer and traceparent helpers
    release_candidates.py                 # Week 12's candidates v2.1 to v2.4
  weeks/
    week-11-evaluation-harness-and-ci/handson/lab.py   # run_suite, write_artifact, verify_artifact (loaded by path)
    week-12-release-gates/handson/lab.py               # gate, release policy, candidates (loaded by path)
    week-14-multi-tenant-governance/handson/lab.py     # tenants, runners, seed (loaded by path)
    week-16-distributed-evaluation-capstone/
      README.md                           # week index
      theory/week-16-distributed-evaluation-capstone-theory.md   (and .html)
      handson/
        week-16-distributed-evaluation-capstone-handson.md       # this file
        week-16-distributed-evaluation-capstone-handson.ipynb    # the same lab as a notebook
        week-16-distributed-evaluation-capstone-adr-001-lease-queue.md
        week-16-distributed-evaluation-capstone-adr-002-tenant-fairness.md
        week-16-distributed-evaluation-capstone-runbook.md
        lab.py                            # queue, admission, simulated day, merge, gate, threads, dashboard
        tests/test_lab.py
        runs/week-16/                     # written by the commands below, git-ignored
      dataset/
        README.md
        queue-policy-v1.json              # workers, lease, attempts, capacity, quotas, budgets, SLOs
        day-script-v1.json                # the SIMULATED day's submissions and fault plan
```

### The notebook

`week-16-distributed-evaluation-capstone-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Run everything from `new_course/` with the course environment active ([setup](../../../setup.md)). The lab uses the standard library only, and the earlier weeks' labs it loads do too. Nothing here calls a model or costs money: every dollar and every second on the simulated day is SIMULATED, and the `threads` command reports wall-clock numbers from your machine.

### The queue's API

The queue is three tables (`jobs`, `job_events`, `requests`) in the same SQLite database as Week 14's platform. The queue's charges land in the platform's `usage` table.

| Function | What it does |
| --- | --- |
| `enqueue(conn, spec, now)` | Inserts a job unless its ID exists. The ID is a hash of the work, so a resend is a no-op |
| `lease(conn, worker, now, scheduler)` | Takes the write lock, picks a job (`fifo` or `fair`), marks it leased until `now + lease_seconds`, raises `lease_token` and `attempts` |
| `complete(conn, leased, result, cost, now)` | Stores the result and inserts one usage row in one transaction, only if the row still has the caller's token. Returns `done` or `stale` |
| `fail(conn, leased, error, now)` | The runner raised: back to the queue after 15 s, then 30 s, or `dead` at the third attempt |
| `expire_leases(conn, now)` | Puts back every job whose lease ran out, without back-off, or marks it dead at the attempt limit |
| `admit(platform, actor, spec, now)` | Week 14's `_authorize`, a registry read of the dataset, then budget, quota and capacity checks. Enqueues the whole request or nothing |
| `merge_shards(skeleton, results, expected, workers, dead)` | One Week 11 `eval-run-v1` artifact from shard artifacts. Refuses shards from other code; missing shards leave it incomplete |
| `simulate(scheduler, out)` | Replays the SIMULATED day on a simulated clock with four workers and the fault plan |
| `thread_trial(path, n_jobs, n_threads)` | The same queue functions in real threads against a SQLite file |

### The day script and the fault plan

`dataset/day-script-v1.json` holds 16 submissions. The support RAG team submits nine retrieval sweeps at t=0 (three retrievers times k = 3, 5 and 10, each five shards of ten queries). The refunds team submits release checks for v2.1 at t=5, the same request again at t=6, v2.3 at t=20 and v2.4 at t=40, and its viewer tries v2.4 at t=30. Trust and safety submits the fault suite on the lax backend at t=10. The support team resends its refused sweep at t=240.

The fault plan is SIMULATED: w2 dies half way through its 4th job, w3 stalls for 100 s on its 6th job and then reports, and the second fault-suite shard makes every worker raise.

### Run it

**The day under fair dispatch.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py demo
```

```text
SIMULATED day, scheduler=fair, 4 workers, lease 60 s, max 3 attempts. Ended at t=600 s.

Admission
   t  actor             request       kind      what          status     detail
   0  rag.engineer      req-55b6274c  retrieval bm25@k3       admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-d5c26b4a  retrieval bm25@k5       admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-504ce191  retrieval bm25@k10      admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-5506d0c5  retrieval concept@k3    admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-6700c316  retrieval concept@k5    admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-fa305c79  retrieval concept@k10   admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-bba692f1  retrieval hybrid@k3     admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-32d7c1b6  retrieval hybrid@k5     admitted   5 jobs, 5 new, reserved 0.0100
   0  rag.engineer      req-e930e6be  retrieval hybrid@k10    denied:quota 40 active + 5 new > 40 for support-rag: retry later
   5  refunds.engineer  req-89b0c5e2  release   v2.1          admitted   12 jobs, 12 new, reserved 0.1800
   6  refunds.engineer  req-89b0c5e2  release   v2.1          duplicate  same request already admitted
  10  safety.engineer   req-1afffaae  suite     stable_key    admitted   2 jobs, 2 new, reserved 0.0165
  20  refunds.engineer  req-39f45f67  release   v2.3          admitted   12 jobs, 6 new, reserved 0.0900
  30  refunds.viewer    req-9af862e4  release   v2.4          denied:role eval.run is not permitted for role viewer
  40  refunds.engineer  req-9af862e4  release   v2.4          denied:budget spent 0.0000 + reserved 0.2700 + this request 0.0900 > 0.3
 240  rag.engineer      req-e930e6be  retrieval hybrid@k10    admitted   5 jobs, 5 new, reserved 0.0100

Requests
request       tenant         kind      what          submitted finished latency  outcome
req-55b6274c  support-rag    retrieval bm25@k3               0       60      60  recall@5 0.74
req-d5c26b4a  support-rag    retrieval bm25@k5               0      130     130  recall@5 0.8
req-504ce191  support-rag    retrieval bm25@k10              0      253     253  recall@5 0.9267
req-5506d0c5  support-rag    retrieval concept@k3            0      340     340  recall@5 0.81
req-6700c316  support-rag    retrieval concept@k5            0      403     403  recall@5 0.8967
req-fa305c79  support-rag    retrieval concept@k10           0      450     450  recall@5 0.9733
req-bba692f1  support-rag    retrieval hybrid@k3             0      510     510  recall@5 0.8133
req-32d7c1b6  support-rag    retrieval hybrid@k5             0      553     553  recall@5 0.9033
req-89b0c5e2  refunds-agent  release   v2.1                  5      250     245  SHIP: every rule passed
req-1afffaae  trust-safety   suite     stable_key           10      103      93  UNFINISHED: incomplete run: 10 of 11 cases (dead-lettered shards: job-aa6554ec60)
req-39f45f67  refunds-agent  release   v2.3                 20      360     340  BLOCK: no-unauthorized-refunds FAIL (release 0, safety_probe 1) cases ['t-015']
req-e930e6be  support-rag    retrieval hybrid@k10          240      600     360  recall@5 0.9633

Queue wait
tenant          jobs  wait p50    p95    max   (SIMULATED seconds)
refunds-agent     18       135    320    320
support-rag       45       313    510    523
trust-safety       2        20     40     40

Charges (Week 14 usage table, SIMULATED dollars)
  support-rag     45 jobs   450 cases  $0.0900 of $0.10
  refunds-agent   18 jobs   180 cases  $0.1740 of $0.30
  trust-safety     1 jobs    10 cases  $0.0120 of $0.06
  usage rows per job: dead x0: 1, done x1: 64
  stale completions rejected: 1, SIMULATED work wasted: $0.0132

SLOs (SIMULATED day)
  met    release decision within 300 s      req-89b0c5e2   measured 245
  BREACH release decision within 300 s      req-39f45f67   measured 340
  BREACH queue wait p95 within 120 s        refunds-agent  measured 320
  BREACH queue wait p95 within 120 s        support-rag    measured 510
  met    queue wait p95 within 120 s        trust-safety   measured 40

Audit chain: 73 events, problems: none
```

Read it top to bottom:

- **Admission.** Eight sweeps fill the support team's quota of 40 active jobs. The ninth is refused, then admitted when resent at t=240. The resent v2.1 request is a duplicate and reserves nothing. v2.3 creates 6 new jobs and reuses v2's 6 baseline shards. The viewer is refused for its role and v2.4 for budget: $0.27 reserved plus $0.09 is over $0.30, although nothing had been spent.
- **Decisions.** v2.1 SHIP and v2.3 BLOCK on the one unauthorized refund in t-015, the verdicts Week 12 gave in one process. Trust and safety's sweep is UNFINISHED, 10 of 11 cases, with the dead job named.
- **Money.** 64 finished jobs have one usage row each and the dead job none. The stalled worker's late result was rejected, and $0.0132 of SIMULATED work ran without being charged to anyone: the crashed attempt and the stalled one.
- **SLOs.** One release decision met its 300 s target and one missed it. Section 9 of the theory explains why that miss is capacity, not scheduling.

**What the fault plan hit.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py faults
```

```text
Jobs hit by the SIMULATED fault plan (job_events):

job-0fef34a3a7 support-rag bm25/retrieval@k10 shard 2/5: final state done, 2 attempts
  t=   0  -    enqueued bm25/retrieval@k10 shard 2/5
  t= 130  w3   leased   attempt 1, token 1
  t= 190  w3   retry    lease expired (w3)
  t= 200  w4   leased   attempt 2, token 2
  t= 230  w4   done     token 2, cost 0.0020
  t= 260  w3   stale    token 1, cost 0.0020

job-4366b8ce3d refunds-agent v2/safety_probe shard 3/3: final state done, 2 attempts
  t=   5  -    enqueued v2/safety_probe shard 3/3
  t=  90  w2   leased   attempt 1, token 1
  t= 150  w2   retry    lease expired (w2)
  t= 160  w4   leased   attempt 2, token 2
  t= 180  w4   done     token 2, cost 0.0112

job-aa6554ec60 trust-safety stable_key/faults shard 2/2: final state dead, 3 attempts
  t=  10  -    enqueued stable_key/faults shard 2/2
  t=  50  w1   leased   attempt 1, token 1
  t=  51  w1   retry    SIMULATED: the runner raised on this shard
  t=  71  w1   leased   attempt 2, token 2
  t=  72  w1   retry    SIMULATED: the runner raised on this shard
  t= 102  w1   leased   attempt 3, token 3
  t= 103  w1   dead     SIMULATED: the runner raised on this shard

Workers: w1 alive (25 leases), w2 DEAD (4 leases), w3 alive (18 leases), w4 alive (22 leases)
Usage rows per job: {('dead', 0): 1, ('done', 1): 64}
```

The three histories are the three recovery paths. The crash came back when its lease expired, with no back-off. The stall came back the same way, and w3's late report at t=260 carried token 1 against the row's token 2, so it was refused. The poison shard came back after 15 s and then 30 s, and died at its third attempt.

**One request's audit trail.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py audit
```

```text
Audit trail for req-39f45f67 (Week 14 hash-chained log, SIMULATED clock):
    50 2026-03-20T09:00:20Z refunds.engineer  eval.run         allow 
    52 2026-03-20T09:00:20Z refunds.engineer  eval.admit       allow refunds-agent/tool-cases@v1 sha256 cea3a4cc2952; 12 jobs (6 new, 6 shared); reserved 0.0900
    66 2026-03-20T09:06:00Z refunds.engineer  release.decided  allow BLOCK; decision sha256 088b872859bc
Chain: intact; anchor seq 72 c0ca9645e43b
```

The trail ties the decision to the dataset version it pinned at admission (`tool-cases@v1`, the hash Week 14 checks on every read) and to the SHA-256 of the `decision.json` it produced. Seq 51, between them, is the dataset read, logged under the dataset's resource. The final event is recorded under the submitter's identity. A production platform would record a service principal acting on the submitter's behalf.

**FIFO against round robin.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py compare
```

```text
Same SIMULATED day, same faults, two dispatch rules.

tenant          fifo p50   p95   max    fair p50   p95   max
refunds-agent        455   510   510         135   320   320
support-rag          180   370   390         313   510   523
trust-safety         470   490   490          20    40    40

release request  candidate  fifo latency fair latency  verdict
req-89b0c5e2     v2.1                495          245  SHIP
req-39f45f67     v2.3                530          340  BLOCK
SLO breaches, fifo: req-89b0c5e2 (495), req-39f45f67 (530), refunds-agent (510), support-rag (370), trust-safety (490)
SLO breaches, fair: req-39f45f67 (340), refunds-agent (320), support-rag (510)
```

Under FIFO, trust and safety waited a median 470 s for a job that runs in 30 s, and both release decisions missed the target. Round robin moved the wait onto the team that created it. The verdicts are the same under both rules: scheduling changes when the evidence arrives, never what it says.

**The dashboard.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py dashboard
```

```text
wrote weeks/week-16-distributed-evaluation-capstone/handson/runs/week-16/dashboard/dashboard.html and 12 traces
```

Open `dashboard.html` in a browser. It shows the SLOs, each team's waits, charges and budget, every request with its result, links to the two release decisions (`runs/week-16/day/<request>/decision/decision.md`) and to each request's redacted trace, the admission denials, the fault histories and the audit head. Every number on it is SIMULATED.

**Real threads.**

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py threads
```

```text
Timer check: time.sleep(0.005) took 99 ms on this machine.
Real threads, SQLite file (WAL), 2000 jobs, 0 ms SIMULATED I/O per job, one worker killed holding a lease.
Wall-clock numbers measured on this machine: prototype measurements, not production capacity.
threads  done  charged  retried  stale  jobs/s  p50 ms  p95 ms
      1  2000     2000        1      0     626    1974    3021
      2  2000     2000        1      0     601    1792    3061
      4  2000     2000        1      0     467    2455    3945
      8  2000     2000        4      3     431    2803    4101
```

Your numbers will differ: they are wall-clock measurements. What should not differ is the `done` and `charged` columns, 2000 each, with the killed worker's job retried. Throughput fell as threads were added, because every lease and completion queues for SQLite's one write lock. At 8 threads, three healthy leases expired while their workers waited for that lock: those jobs ran twice (`stale` 3) and were charged once. `p50 ms` is time in the system from enqueue, and all 2000 jobs were enqueued at once: it measures how long the backlog took to drain, not one job's latency. The timer check explains why no I/O is simulated by default: here a 5 ms sleep took 99 ms, so `--io-ms 5` would measure the operating system's timer batching.

### Capstone acceptance criteria

The roadmap's eight capstone criteria, each with the evidence from Weeks 1 to 16:

| # | Criterion | Evidence | Where |
| --- | --- | --- | --- |
| 1 | Correctness: tests inspect retrieved passages, tool calls, side effects and outcomes | Week 4 retrieval metrics, Week 7 tool and ledger checks, Week 8 trajectory and outcome checks, run on every shard | `datasets/`, Weeks 4, 7, 8 tests; `test_sharded_runs_equal_the_single_process_runs` |
| 2 | Risk: zero unauthorized or duplicate refunds; adversarial and fault tests | Week 12's hard gates on both runs; v2.3 BLOCK on t-015 through the queue; Week 10's fault suite as trust and safety's sweep | `demo`; `test_release_requests_get_the_week_12_verdicts_through_the_queue` |
| 3 | Repeatability: pinned datasets, versions, policy; replayable traces | Admission pins `tool-cases@v1` and its SHA-256; merged run IDs equal single-process run IDs; one trace per request | `audit`; `test_each_request_is_one_trace_across_the_queue` |
| 4 | Release decisions: machine-readable verdict, threshold evidence, slices, reviewer notes | `decision.json` and `decision.md` per release request, hashed into the audit log | `runs/week-16/day/<request>/decision/` |
| 5 | Online operations: sampled traces, monitoring, alerts, rollback | Week 13's replay, alerts and rollback; Week 12's canary | Weeks 12 and 13 labs (not rerun here) |
| 6 | Enterprise controls: three tenants, isolation, roles, audit, budgets, fairness | Week 14's platform; this week's role, budget, quota and capacity checks and round-robin dispatch | `compare`; `test_admission_checks_role_budget_quota_and_duplicates`, `test_fair_dispatch_protects_the_quiet_tenants_from_the_flood` |
| 7 | Reliability: retries, timeouts and partial failures neither double-charge nor lose runs | Lease expiry, token-fenced completion, dead letters, unfinished runs, one usage row per job | `faults`; the crash, stall, poison and charge tests; both drills |
| 8 | Staff review: architecture diagram, 2 ADRs, demo, performance and cost estimates, runbook | Theory section 10, the two ADRs, the demo script below, the estimate below, the runbook | This folder |

Criterion 5 is evidenced by Weeks 12 and 13, not by this week's code: the queue produces release decisions, and the canary and online checks happen after a SHIP.

### Performance and cost estimates

Two kinds of number come out of this lab, and neither is a production capacity figure.

- **Simulated.** The day's seconds come from fixed costs per case (3 s per retrieval query, 2 s per tools case, 3 s per fault case) and its dollars from Week 11's and Week 14's SIMULATED prices. They show how leases, quotas and dispatch rules behave.
- **Prototype measurements.** The thread trial measured roughly 430 to 630 queue operations per second on one machine, a ceiling set by SQLite's single writer.

A production estimate takes the same structure with measured inputs. Workers needed = (job-seconds submitted per hour) ÷ (3,600 × target utilisation). With the simulated day's burst of about 1,593 job-seconds arriving once an hour and a 60% target utilisation, that is 1,593 ÷ 2,160 ≈ 0.74 workers on average. The SLO says otherwise: on the simulated day four workers decided one of the two release checks within 300 s and six decided both. Bursts, not averages, size the pool. Replace each simulated input with a measurement before quoting either figure: model latency and cost per case from Week 11 runs with a live model, submissions per hour per team from the platform's own logs, and a load test on the real queue.

### Demo script

A 10-minute demo for a design review, in this order:

1. **The problem.** Show the `compare` output: under FIFO, a 30 s trust and safety job waited 470 s and both release decisions missed 300 s.
2. **Admission.** In the `demo` output, point at the quota refusal and resend, the duplicate, the role refusal and the budget refusal with its arithmetic.
3. **A complete release decision.** Open `runs/week-16/day/req-39f45f67/decision/decision.md` from the dashboard: BLOCK on t-015. Then show the request's audit trail with the dataset hash and the decision hash.
4. **Faults.** Show the `faults` output: a crash recovered by lease expiry, a late result refused by its token, a poison shard dead-lettered and its run marked unfinished.
5. **Money.** Show `usage rows per job: dead x0: 1, done x1: 64` and the $0.0132 of uncharged rerun work.
6. **Limits.** Show the v2.3 SLO breach and the capacity floor, then the thread trial's flat throughput, and say which numbers are simulated, which are measured, and what replaces SQLite (ADR-001).

### Exercises

1. **Capacity.** Add `"w5", "w6"` to `workers` in `dataset/queue-policy-v1.json` and rerun `demo`. Does v2.3 meet its SLO? Does the refunds team's p95 wait?
2. **A lease shorter than a job.** Set `lease_seconds` to 15 and rerun `demo`. Predict what happens to a 20-second tools shard before you look.
3. **No retries.** Set `max_attempts` to 1. What happens to v2.1's verdict, and why is that verdict correct?
4. **Quota against fairness.** Restore the policy, set the support team's `max_active_jobs` to 15, and run `compare`. How do the FIFO release latencies change, and what did the support team lose?
5. **A budget without reservations.** In the notebook, run `simulate("fair", RUNS / "loose", check_reserved=False)`. Is v2.4 admitted? What does the gate say about it, and what did the refunds team end up paying?
6. **Backpressure.** Set `capacity` to 12. Submit v2.1's release check, then trust and safety's sweep. What answer does the sweep get, and what should its client do? (`test_a_full_queue_refuses_new_work` does this.)
7. **A worker on other code.** In the notebook, take v2.1's three v2 release shards, change one result's `run_id`, and call `merge_shards`. What happens, and why is that the right behaviour during a rolling deployment?

Restore `queue-policy-v1.json` after each change (`git checkout` the file), or the tests fail.

### Reading a failed check

The tests pin the simulated day's numbers, because the day is deterministic. A failure that changes a wait or a latency by a few seconds after a policy edit is the edit working. A failure in `charges` (a job with 0 or 2 usage rows), in the merge equality test, or in a verdict is a correctness bug: find the job in `job_events` and walk its history. The thread test asserts only counts, never timings, so it should not fail on a slow machine. If it does, a job was lost or charged twice under real concurrency.

## 2. Two debugging drills

### Drill 1: the worker that charged inside the job

**Broken change.** A developer reuses Week 14's `run_eval` inside the worker, because it already runs an evaluation and charges the team (`run_job_through_platform`).

**Symptom.** The worker dies after `run_eval` returns and before it reports. The lease expires and a second worker runs the job again:

```text
broken: [('run-0001', 'refunds-agent', 30, 0.0288), ('run-0002', 'refunds-agent', 30, 0.0288)]
fixed:  [('job-drill-1', 'refunds-agent', 30, 0.0288)]
```

`test_drill_1_charging_inside_the_job_double_charges_a_retried_job` pins both lines.

**Diagnosis.** One job, two usage rows, under two different run IDs. The unique index on the job column could not catch that. The charge happened when the work ran, outside the queue's completion transaction, and every attempt makes a new run ID. Search `job_events` for the job: two `leased` events and one `done`, so the second charge has no completion behind it.

**Fix and verify.** The worker runs the job with `execute`, which charges nothing, and `complete` inserts the charge keyed by the job ID, in the same transaction as the result, under the lease token. Rerun the drill: one row, `job-drill-1`.

### Drill 2: the merge that lost a case

**Broken change.** `merge_present_shards` builds the expected case list from the shards that came back.

**Symptom.** On trust and safety's sweep, where one shard was dead-lettered:

```text
broken complete=True 10 of 10 cases, stop_reason=None
fixed  complete=False 10 of 11 cases, stop_reason=dead-lettered shards: job-aa6554ec60
```

The broken artifact passes `verify_artifact`, and case f-011 is gone from the evidence. `test_drill_2_merging_only_present_shards_hides_the_lost_case` asserts both and names the lost case.

**Diagnosis.** Compare the artifact's `expected_cases` with the number of cases in the request's plan: 10 against 11. A run that is smaller than its plan and still says complete has lost evidence silently. For a release check the gate would then compare a 20-case candidate with a 30-case baseline and HOLD on comparability. For a run nobody compares, nothing would notice.

**Fix and verify.** `merge_shards` takes the expected list from the planned shards' cases and names the dead jobs in `stop_reason`. Rerun the drill: `complete=False 10 of 11`, and Week 11's `verify_artifact` reports `incomplete run: 10 of 11 cases (dead-lettered shards: job-aa6554ec60)`.

## 3. Completion criteria

- [ ] `python3 -m pytest weeks/week-16-distributed-evaluation-capstone` passes: 19 tests.
- [ ] `demo` shows v2.1 SHIP, v2.3 BLOCK on t-015, the trust and safety sweep UNFINISHED at 10 of 11, and `usage rows per job: dead x0: 1, done x1: 64`.
- [ ] You can explain each of the three job histories in `faults`, including why w3's result at t=260 was refused.
- [ ] You can do the budget arithmetic behind v2.4's refusal and the capacity arithmetic behind v2.3's SLO breach by hand.
- [ ] `compare` shows FIFO starving trust and safety and round robin moving the wait to the support team.
- [ ] `threads` finishes every job with one charge each on your machine, and you can say why more threads did not help.
- [ ] You have read both ADRs and the runbook, and can answer the theory's design review out loud.
- [ ] Both drills reproduce the broken output and the fix.

## 4. Solutions

1. **Capacity.** With six workers the day ends at t=370. v2.1 decides in 156 s and v2.3 in 200 s, both inside 300 s. The refunds team's p95 wait drops to 180 s, still over the 120 s target: about 1,600 job-seconds of work arrived in 40 s, and six workers need about 265 s to clear it. Meeting the wait SLO needs more workers again, or a smaller sweep quota.
2. **A lease shorter than a job.** Every tools shard (20 s), sweep shard (30 s) and fault shard (30 s) outlives its 15 s lease. Each is put back, rerun, expires again, and is dead-lettered at the third attempt: 60 dead jobs, 176 refused late results, both release checks HOLD, and $0.798 of SIMULATED work charged to nobody. The fix is a lease above the longest job, or workers that renew their lease while running.
3. **No retries.** v2.1 becomes HOLD: the crashed v2 safety-probe shard is dead at its first attempt. v2's probe run is 20 of 30 cases, and the gate refuses to compare incomplete evidence. HOLD is correct, because nobody knows what the missing ten cases would have shown. v2.3 stays BLOCK, since its unauthorized refund is in the cases that did run.
4. **Quota against fairness.** With the support quota at 15, six of its nine sweeps are refused at t=0 (and one is admitted when resent). Under FIFO, v2.1 decides in 235 s and v2.3 in 281 s, both inside the target, and trust and safety's p50 wait falls from 470 s to 210 s. The support team paid for it with refused work it must resubmit. A quota protects others at admission. Round robin protects them at dispatch without refusing anything.
5. **A budget without reservations.** v2.4 is admitted at t=40, because only spending ($0.0000) is compared with the budget. Its check ends in HOLD on the soft cost gate (`cost-increase FAIL (release 1.264)`, as in Week 12). The refunds team was charged $0.2468, under $0.30 only because the reservation per case ($0.0015) overestimates the actual cost (about $0.001). With a less cautious estimate, or a pricier candidate, the team would have overspent with nothing to stop it.
6. **Backpressure.** The sweep gets `denied`, reason `capacity`: `12 active + 2 new > queue capacity 12: retry later`. Its client should wait and resubmit the same request. Because request and job IDs are hashes, the resend creates nothing twice.
7. **A worker on other code.** `merge_shards` raises `ValueError: shards ran other code or data: ['run-000000000000'], expected run-9e026fba7982`. During a rolling deployment some workers run old code. Their shards carry a different run ID, because Week 11's run ID hashes the code, and merging them would build one run out of two versions. Refusing the merge turns version skew into a rerun instead of a quietly mixed result.

For the design-review questions, see the [theory's design review](../theory/week-16-distributed-evaluation-capstone-theory.md#12-design-review).
