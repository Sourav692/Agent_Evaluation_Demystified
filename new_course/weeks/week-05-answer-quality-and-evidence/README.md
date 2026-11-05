# Week 5: Answer quality and evidence

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-05-answer-quality-and-evidence-theory.md) ([HTML](theory/week-05-answer-quality-and-evidence-theory.html)) | Goals, three answers that look fine, faithfulness, citations, correctness, relevance, abstention, stale and restricted sources, separating retrieval from generation, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-05-answer-quality-and-evidence-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-05-answer-quality-and-evidence-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The data this week's lab reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report --retrieval filtered
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py case a-009
python3 -m pytest weeks/week-05-answer-quality-and-evidence        # 12 tests
```
