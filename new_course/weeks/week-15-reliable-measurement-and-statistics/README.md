# Week 15: Reliable measurement and statistics

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-15-reliable-measurement-and-statistics-theory.md) ([HTML](theory/week-15-reliable-measurement-and-statistics-theory.html)) | A 2-point gain that might be noise, where variation comes from, Wilson intervals, bootstrap resampling, paired comparisons and McNemar's test, sample size and power, repeated runs, judge calibration against two reviewers, segments and mix shift, the reliability report, the release run by hand, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-15-reliable-measurement-and-statistics-handson.md) | The lab walkthrough with real output, the report's fields, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-15-reliable-measurement-and-statistics-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The SIMULATED stochastic experiment, reviewer B's AUTHORED review sheet, and the course-root files this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py repeat
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare --runs 20 --first-run 0
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py agreement
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py segments
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py report --out weeks/week-15-reliable-measurement-and-statistics/handson/runs/week-15
python3 -m pytest weeks/week-15-reliable-measurement-and-statistics        # 17 tests
```
