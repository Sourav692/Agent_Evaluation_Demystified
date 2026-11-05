# Week 8: Trajectories and task completion

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-08-trajectories-and-task-completion-theory.md) ([HTML](theory/week-08-trajectories-and-task-completion-theory.html)) | Goals, two runs the reply cannot tell apart, traces, exact and flexible matching, required and forbidden steps, task success from the ledger, efficiency, partial credit behind a hard gate, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-08-trajectories-and-task-completion-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-08-trajectories-and-task-completion-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The shared data this week reads, with its provenance |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py match
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py case --agent refund_first --case tr-031
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py scorecard
python3 -m pytest weeks/week-08-trajectories-and-task-completion        # 12 tests
```
