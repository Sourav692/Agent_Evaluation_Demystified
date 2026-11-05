# Week 9: Multi-turn state

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-09-multi-turn-state-theory.md) ([HTML](theory/week-09-multi-turn-state-theory.html)) | Goals, a refund lost on restart and one leaked to another customer, sessions and state, checkpoints and restarts, clarification, long conversations, tenant isolation, state checks against exact text, the 25 scenarios, the results, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-09-multi-turn-state-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-09-multi-turn-state-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The frozen v2 transcripts, and the shared scenarios this week reads |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-09-multi-turn-state/handson/lab.py report --agent v1
python3 weeks/week-09-multi-turn-state/handson/lab.py show conv-16 --agent v1 --backend lax
python3 weeks/week-09-multi-turn-state/handson/lab.py invariance --agent v2
python3 weeks/week-09-multi-turn-state/handson/lab.py wording
python3 -m pytest weeks/week-09-multi-turn-state        # 13 tests
```
