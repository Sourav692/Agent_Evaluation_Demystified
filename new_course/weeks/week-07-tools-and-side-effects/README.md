# Week 7: Tools and persisted side effects

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-07-tools-and-side-effects-theory.md) ([HTML](theory/week-07-tools-and-side-effects-theory.html)) | Goals, two refunds that look fine, tools, traces and the ledger, authentication and authorization, argument checks, tool responses, read-back, severity, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-07-tools-and-side-effects-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-07-tools-and-side-effects-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The shared data this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-07-tools-and-side-effects/handson/lab.py matrix
python3 weeks/week-07-tools-and-side-effects/handson/lab.py report --agent v1 --backend strict
python3 weeks/week-07-tools-and-side-effects/handson/lab.py case t-016 --agent v1 --backend strict
python3 -m pytest weeks/week-07-tools-and-side-effects        # 11 tests
```
