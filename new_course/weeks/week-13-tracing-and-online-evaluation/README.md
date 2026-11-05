# Week 13: Tracing and online evaluation

Work through the folders in this order:

| Folder | Contents |
|---|---|
| [`theory/`](theory/week-13-tracing-and-online-evaluation-theory.md) ([HTML](theory/week-13-tracing-and-online-evaluation-theory.html)) | Goals, a deploy that told customers their refund failed, traces and spans, OpenInference conventions, context propagation, reference-free online checks, alerts, rollback triggers, sampling, feedback and drift, redaction, the dashboard, design-review questions and a memory card. No commands |
| [`handson/`](handson/week-13-tracing-and-online-evaluation-handson.md) | The lab walkthrough with real output, exercises, two debugging drills, the completion checklist and solutions. Also the [operations runbook](handson/week-13-tracing-and-online-evaluation-runbook.md), `lab.py`, the same lab as a notebook (`week-13-tracing-and-online-evaluation-handson.ipynb`) and `tests/` |
| [`dataset/`](dataset/README.md) | The SIMULATED traffic configuration and the online policy: alerts, rollback rule, sampling and redaction |

Run from `new_course/`, with the course environment active (see [setup](../../setup.md)):

```bash
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py trace r-3211
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py sampling
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py dashboard
python3 -m pytest weeks/week-13-tracing-and-online-evaluation        # 13 tests
```

The optional `otel` command needs `opentelemetry-sdk==1.45.2` from [`requirements-integrations.txt`](../../requirements-integrations.txt). It is free and calls no service.
