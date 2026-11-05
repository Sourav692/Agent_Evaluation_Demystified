# Week 10: Faults, adversarial inputs and handoffs

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-10-faults-adversarial-and-handoffs-theory.md) ([HTML](theory/week-10-faults-adversarial-and-handoffs-theory.html)) | Goals, a retry that refunded twice, timeouts and partial failure, idempotency, duplicate requests, the fault sweep, prompt injection and malicious tool content, routing and handoffs, failed handoffs, the severity report, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-10-faults-adversarial-and-handoffs-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-10-faults-adversarial-and-handoffs-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The shared fault, handoff and poisoned-chunk files this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py case f-001 --agent naive_retry --backend lax
python3 weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py sweep
python3 weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py suite
python3 weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py handoffs
python3 -m pytest weeks/week-10-faults-adversarial-and-handoffs        # 13 tests
```
