# Week 11: Evaluation harness and CI

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-11-evaluation-harness-and-ci-theory.md) ([HTML](theory/week-11-evaluation-harness-and-ci-theory.html)) | Goals, three green results that proved nothing, reproducibility and pins, the run artifact, exit codes, parallel runs and isolation, caching, budgets, flaky results, CI with blocking and opt-in jobs, two artifacts read by hand, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-11-evaluation-harness-and-ci-handson.md) | The lab walkthrough with real output, the artifact's field reference, exercises, two debugging drills, the completion checklist and solutions. Also `lab.py`, the same lab as a notebook (`week-11-evaluation-harness-and-ci-handson.ipynb`), the example CI workflow (`ci/week-11-eval-workflow.yml`) and `tests/` |
| [`dataset/`](dataset/README.md) | The pinned course-root inputs this week reads, and the artifact it writes |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py pins
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py run --suite tools --agent v2 --out weeks/week-11-evaluation-harness-and-ci/handson/runs/tools-v2-strict
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py verify weeks/week-11-evaluation-harness-and-ci/handson/runs/tools-v2-strict
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py flaky --suite tools --agent v2 --repeat 20
python3 -m pytest weeks/week-11-evaluation-harness-and-ci        # 15 tests
```
