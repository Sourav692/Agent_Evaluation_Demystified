# Week 14: Multi-tenant governance

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-14-multi-tenant-governance-theory.md) ([HTML](theory/week-14-multi-tenant-governance-theory.html)) | Goals, a shared script that read another team's tickets, tenancy models, the tenant taken from the identity, roles and separation of duties, denials that do not leak, the versioned registry and grants, redaction before storage, the hash-chained audit log and its anchor, attribution and budgets, isolation trade-offs, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-14-multi-tenant-governance-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-14-multi-tenant-governance-handson.ipynb`) and `tests/`. The platform itself is [`shared/governance.py`](../../shared/governance.py) |
| [`dataset/`](dataset/README.md) | The tenant policy, the three teams' evaluators, and 8 escalation queries with synthetic personal data |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py demo
python3 weeks/week-14-multi-tenant-governance/handson/lab.py access
python3 weeks/week-14-multi-tenant-governance/handson/lab.py probe
python3 weeks/week-14-multi-tenant-governance/handson/lab.py registry
python3 weeks/week-14-multi-tenant-governance/handson/lab.py redaction
python3 weeks/week-14-multi-tenant-governance/handson/lab.py audit
python3 weeks/week-14-multi-tenant-governance/handson/lab.py usage
python3 -m pytest weeks/week-14-multi-tenant-governance        # 17 tests
```

Everything is local, free and standard library. Teams, people, budgets and costs are fictional or SIMULATED.
