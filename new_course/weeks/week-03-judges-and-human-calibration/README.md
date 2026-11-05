# Week 3: Model judges and human calibration

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-03-judges-and-human-calibration-theory.md) ([HTML](theory/week-03-judges-and-human-calibration-theory.html)) | Goals, a concrete failure, the concepts, a worked example, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-03-judges-and-human-calibration-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-03-judges-and-human-calibration-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The data this week's lab reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py prompt case-0024
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py pairwise
python3 -m pytest weeks/week-03-judges-and-human-calibration        # 15 tests
```
