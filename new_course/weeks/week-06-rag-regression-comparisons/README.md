# Week 6: RAG regression comparisons

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-06-rag-regression-comparisons-theory.md) ([HTML](theory/week-06-rag-regression-comparisons-theory.html)) | Goals, a better average with a worse main path, fair comparisons, the scorecard, slices and pairs, the gold-context swap, ablation, drift, the release decision, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-06-rag-regression-comparisons-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-06-rag-regression-comparisons-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The shared data this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py scorecard --candidate v2
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py slices --candidate v2
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py decide --candidate v2.1
python3 -m pytest weeks/week-06-rag-regression-comparisons        # 10 tests
```
