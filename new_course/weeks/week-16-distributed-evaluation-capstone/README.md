# Week 16: Distributed evaluation capstone

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-16-distributed-evaluation-capstone-theory.md) ([HTML](theory/week-16-distributed-evaluation-capstone-theory.html)) | Goals, a release decision stuck behind a sweep, queues and leases, fencing tokens, at-least-once execution with exactly-once effects, retries and dead letters, admission control and backpressure, fairness between teams, sharding and merging evidence, traces and audit, SLOs and capacity, the capstone architecture, worked examples, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-16-distributed-evaluation-capstone-handson.md) | The lab walkthrough with real output, the capstone acceptance checklist, performance and cost estimates, a demo script, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-16-distributed-evaluation-capstone-handson.ipynb`), `tests/`, [ADR-001](handson/week-16-distributed-evaluation-capstone-adr-001-lease-queue.md), [ADR-002](handson/week-16-distributed-evaluation-capstone-adr-002-tenant-fairness.md) and the [runbook](handson/week-16-distributed-evaluation-capstone-runbook.md) |
| [`dataset/`](dataset/README.md) | The queue policy (workers, lease, attempts, quotas, budgets, SLOs) and the SIMULATED day's submissions and fault plan |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py demo
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py compare
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py faults
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py audit
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py dashboard
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py threads
python3 -m pytest weeks/week-16-distributed-evaluation-capstone        # 19 tests
```

Everything is local, free and standard library. The day, its workers, faults, seconds and dollars are SIMULATED. `threads` reports wall-clock prototype measurements from your machine, not production capacity.
