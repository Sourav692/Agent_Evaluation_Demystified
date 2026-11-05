# Week 2: Golden datasets and test design

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-02-golden-datasets-theory.md) ([HTML](theory/week-02-golden-datasets-theory.html)) | Goals, a concrete failure, the concepts, a worked example, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-02-golden-datasets-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-02-golden-datasets-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The data this week's lab reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-02-golden-datasets/handson/lab.py validate
python3 weeks/week-02-golden-datasets/handson/lab.py slices
python3 weeks/week-02-golden-datasets/handson/lab.py leak-check weeks/week-02-golden-datasets/dataset/few_shot_prompt.md
python3 -m pytest weeks/week-02-golden-datasets        # 16 tests
```
