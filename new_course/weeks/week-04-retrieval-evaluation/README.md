# Week 4: Retrieval evaluation

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-04-retrieval-evaluation-theory.md) ([HTML](theory/week-04-retrieval-evaluation-theory.html)) | Goals, two search failures, the five metrics, hand calculations, retrievers, filters, chunk size, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-04-retrieval-evaluation-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-04-retrieval-evaluation-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The data this week's lab reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-04-retrieval-evaluation/handson/lab.py hand
python3 weeks/week-04-retrieval-evaluation/handson/lab.py compare
python3 weeks/week-04-retrieval-evaluation/handson/lab.py slices --retriever hybrid --k 5
python3 -m pytest weeks/week-04-retrieval-evaluation        # 12 tests
```
