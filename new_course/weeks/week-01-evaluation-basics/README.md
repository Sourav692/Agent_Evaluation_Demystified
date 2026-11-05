# Week 1: Evaluation lifecycle and basic metrics

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-01-evaluation-basics-theory.md) ([HTML](theory/week-01-evaluation-basics-theory.html)) | Goals, a concrete failure, the concepts, a worked example, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-01-evaluation-basics-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-01-evaluation-basics-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The data this week's lab reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-01-evaluation-basics/handson/lab.py
python3 weeks/week-01-evaluation-basics/handson/lab.py --case case-0024
python3 -m pytest weeks/week-01-evaluation-basics        # 12 tests
```
