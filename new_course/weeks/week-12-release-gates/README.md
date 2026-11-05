# Week 12: Release gates

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-12-release-gates-theory.md) ([HTML](theory/week-12-release-gates-theory.html)) | Goals, a candidate as good as v2 with one refund to the wrong customer, hard and soft gates, the release run and the safety probe, quality thresholds, paired comparisons and slice thresholds, evidence and missing inputs, the policy as data, canary and rollback, three decisions by hand, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-12-release-gates-handson.md) | The lab walkthrough with real output, the policy and decision-report field references, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-12-release-gates-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The release policy, the SIMULATED canary metrics, and the course-root files this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-12-release-gates/handson/lab.py scenarios
python3 weeks/week-12-release-gates/handson/lab.py run --agent v2 --out weeks/week-12-release-gates/handson/runs/v2
python3 weeks/week-12-release-gates/handson/lab.py run --agent v2.3 --out weeks/week-12-release-gates/handson/runs/v2.3
python3 weeks/week-12-release-gates/handson/lab.py gate --baseline weeks/week-12-release-gates/handson/runs/v2 --candidate weeks/week-12-release-gates/handson/runs/v2.3 --out weeks/week-12-release-gates/handson/runs/report-v2.3
python3 weeks/week-12-release-gates/handson/lab.py canary
python3 -m pytest weeks/week-12-release-gates        # 15 tests
```
