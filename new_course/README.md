# Enterprise RAG and agent evaluation

A 16-week track that teaches evaluation on one system: a customer-support agent that handles refund requests. It starts with three string checks and ends with a simulated evaluation platform shared by three teams. The [roadmap](enterprise-rag-agent-evaluation-roadmap.md) lists every week's topics, and the [materials plan](materials-creation-plan.md) describes how the track is being written.

**Status:** All five phases, Weeks 1 to 16, are written.

## Before you start

You need basic Python, JSON and command-line skills, and Python 3.12 or later. Read the [setup primer](setup.md) first. It installs the environment and explains retrieval-augmented generation, model calls and agent tool calls for readers new to them. The [glossary](glossary.md) defines every term the guides use.

Every lab runs offline, with no API key and no cost. Optional live exercises are marked in their guides, with the credentials, the number of calls and their validation status stated before any command.

## Study order

Work through the weeks in order. Each one extends the previous week's project.

| Week | Topic | Theory | Hands-on | Dataset |
|---|---|---|---|---|
| 1 | Evaluation lifecycle and basic metrics | [Theory](weeks/week-01-evaluation-basics/theory/week-01-evaluation-basics-theory.md) | [Hands-on](weeks/week-01-evaluation-basics/handson/week-01-evaluation-basics-handson.md) | [Dataset](weeks/week-01-evaluation-basics/dataset/README.md) |
| 2 | Golden datasets and test design | [Theory](weeks/week-02-golden-datasets/theory/week-02-golden-datasets-theory.md) | [Hands-on](weeks/week-02-golden-datasets/handson/week-02-golden-datasets-handson.md) | [Dataset](weeks/week-02-golden-datasets/dataset/README.md) |
| 3 | Model judges and human calibration | [Theory](weeks/week-03-judges-and-human-calibration/theory/week-03-judges-and-human-calibration-theory.md) | [Hands-on](weeks/week-03-judges-and-human-calibration/handson/week-03-judges-and-human-calibration-handson.md) | [Dataset](weeks/week-03-judges-and-human-calibration/dataset/README.md) |
| 4 | Retrieval evaluation | [Theory](weeks/week-04-retrieval-evaluation/theory/week-04-retrieval-evaluation-theory.md) | [Hands-on](weeks/week-04-retrieval-evaluation/handson/week-04-retrieval-evaluation-handson.md) | [Dataset](weeks/week-04-retrieval-evaluation/dataset/README.md) |
| 5 | Answer quality and evidence | [Theory](weeks/week-05-answer-quality-and-evidence/theory/week-05-answer-quality-and-evidence-theory.md) | [Hands-on](weeks/week-05-answer-quality-and-evidence/handson/week-05-answer-quality-and-evidence-handson.md) | [Dataset](weeks/week-05-answer-quality-and-evidence/dataset/README.md) |
| 6 | RAG regression comparisons | [Theory](weeks/week-06-rag-regression-comparisons/theory/week-06-rag-regression-comparisons-theory.md) | [Hands-on](weeks/week-06-rag-regression-comparisons/handson/week-06-rag-regression-comparisons-handson.md) | [Dataset](weeks/week-06-rag-regression-comparisons/dataset/README.md) |
| 7 | Tools and persisted side effects | [Theory](weeks/week-07-tools-and-side-effects/theory/week-07-tools-and-side-effects-theory.md) | [Hands-on](weeks/week-07-tools-and-side-effects/handson/week-07-tools-and-side-effects-handson.md) | [Dataset](weeks/week-07-tools-and-side-effects/dataset/README.md) |
| 8 | Trajectories and task completion | [Theory](weeks/week-08-trajectories-and-task-completion/theory/week-08-trajectories-and-task-completion-theory.md) | [Hands-on](weeks/week-08-trajectories-and-task-completion/handson/week-08-trajectories-and-task-completion-handson.md) | [Dataset](weeks/week-08-trajectories-and-task-completion/dataset/README.md) |
| 9 | Multi-turn state | [Theory](weeks/week-09-multi-turn-state/theory/week-09-multi-turn-state-theory.md) | [Hands-on](weeks/week-09-multi-turn-state/handson/week-09-multi-turn-state-handson.md) | [Dataset](weeks/week-09-multi-turn-state/dataset/README.md) |
| 10 | Faults, adversarial inputs and handoffs | [Theory](weeks/week-10-faults-adversarial-and-handoffs/theory/week-10-faults-adversarial-and-handoffs-theory.md) | [Hands-on](weeks/week-10-faults-adversarial-and-handoffs/handson/week-10-faults-adversarial-and-handoffs-handson.md) | [Dataset](weeks/week-10-faults-adversarial-and-handoffs/dataset/README.md) |
| 11 | Evaluation harness and CI | [Theory](weeks/week-11-evaluation-harness-and-ci/theory/week-11-evaluation-harness-and-ci-theory.md) | [Hands-on](weeks/week-11-evaluation-harness-and-ci/handson/week-11-evaluation-harness-and-ci-handson.md) | [Dataset](weeks/week-11-evaluation-harness-and-ci/dataset/README.md) |
| 12 | Release gates | [Theory](weeks/week-12-release-gates/theory/week-12-release-gates-theory.md) | [Hands-on](weeks/week-12-release-gates/handson/week-12-release-gates-handson.md) | [Dataset](weeks/week-12-release-gates/dataset/README.md) |
| 13 | Tracing and online evaluation | [Theory](weeks/week-13-tracing-and-online-evaluation/theory/week-13-tracing-and-online-evaluation-theory.md) | [Hands-on](weeks/week-13-tracing-and-online-evaluation/handson/week-13-tracing-and-online-evaluation-handson.md) | [Dataset](weeks/week-13-tracing-and-online-evaluation/dataset/README.md) |
| 14 | Multi-tenant governance | [Theory](weeks/week-14-multi-tenant-governance/theory/week-14-multi-tenant-governance-theory.md) | [Hands-on](weeks/week-14-multi-tenant-governance/handson/week-14-multi-tenant-governance-handson.md) | [Dataset](weeks/week-14-multi-tenant-governance/dataset/README.md) |
| 15 | Reliable measurement and statistics | [Theory](weeks/week-15-reliable-measurement-and-statistics/theory/week-15-reliable-measurement-and-statistics-theory.md) | [Hands-on](weeks/week-15-reliable-measurement-and-statistics/handson/week-15-reliable-measurement-and-statistics-handson.md) | [Dataset](weeks/week-15-reliable-measurement-and-statistics/dataset/README.md) |
| 16 | Distributed evaluation capstone | [Theory](weeks/week-16-distributed-evaluation-capstone/theory/week-16-distributed-evaluation-capstone-theory.md) | [Hands-on](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-handson.md) | [Dataset](weeks/week-16-distributed-evaluation-capstone/dataset/README.md) |

Every week has the same three folders, plus a `README.md` index:

- `theory/<week>-theory.md` and its rendered `<week>-theory.html`: goals, a concrete failure, the concepts, a worked example, design-review questions and a memory card. Read it first. It has no commands.
- `handson/`: `<week>-handson.md` (lab walkthrough with real output, exercises, two debugging drills, completion checklist, solutions), `lab.py`, the same lab as a notebook (`<week>-handson.ipynb`) and `tests/`.
- `dataset/`: the data the week's lab reads, with a `README.md` on its fields and provenance.

Attempt the exercises before you read the solutions at the end of the hands-on file.

## Run commands

From `new_course/`, after following the [setup primer](setup.md):

```bash
# Week 1: run agent v1 on 30 labeled cases
python3 weeks/week-01-evaluation-basics/handson/lab.py
python3 weeks/week-01-evaluation-basics/handson/lab.py --case case-0024

# Week 2: validate the dataset, report by slice, check a prompt for holdout leakage
python3 weeks/week-02-golden-datasets/handson/lab.py validate
python3 weeks/week-02-golden-datasets/handson/lab.py slices
python3 weeks/week-02-golden-datasets/handson/lab.py leak-check weeks/week-02-golden-datasets/dataset/few_shot_prompt.md

# Week 3: inspect the judge prompt, compare judge and human labels, check position bias
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py prompt case-0024
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py pairwise

# Week 4: retrieval metrics by hand, then three retrievers, a filter and chunk sizes
python3 weeks/week-04-retrieval-evaluation/handson/lab.py hand
python3 weeks/week-04-retrieval-evaluation/handson/lab.py compare

# Week 5: seven evidence checks on 24 answers, with fixed and with filtered evidence
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report --retrieval filtered

# Week 6: compare v1 with v2, find what regressed and why, decide
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py scorecard --candidate v2
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py decide --candidate v2.1

# Week 7: tool calls and an independent ledger read-back, on a strict and a lax backend
python3 weeks/week-07-tools-and-side-effects/handson/lab.py matrix

# Week 8: trajectory invariants, task success and gated partial credit
python3 weeks/week-08-trajectories-and-task-completion/handson/lab.py scorecard

# Week 9: replay 25 conversations with restarts, checking state rather than wording
python3 weeks/week-09-multi-turn-state/handson/lab.py report

# Week 10: retries, idempotency, injected policy text and handoffs
python3 weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py retry

# Week 11: a pinned, cached, parallel run that leaves a verifiable artifact
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py run --suite tools --agent v2 --out weeks/week-11-evaluation-harness-and-ci/handson/runs/tools-v2-strict
python3 weeks/week-11-evaluation-harness-and-ci/handson/lab.py verify weeks/week-11-evaluation-harness-and-ci/handson/runs/tools-v2-strict

# Week 12: gate four candidates against v2 with a machine-readable release policy
python3 weeks/week-12-release-gates/handson/lab.py scenarios

# Week 13: replay 14 simulated days with traces, alerts and a rollback
python3 weeks/week-13-tracing-and-online-evaluation/handson/lab.py replay

# Week 14: three teams on one evaluation platform: permissions, denials, registry, audit, usage
python3 weeks/week-14-multi-tenant-governance/handson/lab.py demo

# Week 15: is v2's 2-point gain real? Paired bootstrap, sample size and a reliability report
python3 weeks/week-15-reliable-measurement-and-statistics/handson/lab.py compare

# Week 16: a simulated day on the multi-tenant worker queue, ending in two release decisions
python3 weeks/week-16-distributed-evaluation-capstone/handson/lab.py demo

# Tests for every written week (222 tests), with .venv active
python3 -m pytest
```

Run pytest only from `new_course/`. Its `pytest.ini` limits collection to `weeks/`. Run from the repository root, pytest would also collect other folders' test files, which call paid models.

## What is in this folder

```text
new_course/
  README.md                       this page
  setup.md                        environment and background primer
  glossary.md                     every term, with the week that introduces it
  coverage.md                     roadmap concept -> lesson section -> exercise -> evidence
  requirements-core.txt           pytest, ipykernel, markdown; the labs use only the standard library
  requirements-integrations.txt   optional integrations: paid model clients, and the free OpenTelemetry SDK
  pytest.ini                      keeps pytest inside this course
  tools/
    build_html.py                 renders theory Markdown to HTML through site/build.py, in the field-guide format
  shared/
    support_agent.py              refund agent v1: deterministic, with five deliberate bugs
    retrieval.py                  help-centre corpus, chunkers, bm25, concept-vector and hybrid retrievers
    answerer.py                   answer writers v1 and v2, extractive and deterministic
    rag_pipeline.py               RAG versions v1, v2 and v2.1, with SIMULATED cost and latency
    refund_store.py               the SQLite refund ledger, the system of record from Week 7 on
    tools.py                      tool runtime and backend: strict or lax, faults, idempotency keys
    tool_agent.py                 tool agents v1 (deliberate bugs) and v2 (reference)
    trajectory_agents.py          Week 8's plan variants
    session_agent.py              Week 9's multi-turn agents and checkpoint store
    fault_agents.py               Week 10's retry and injection variants
    handoff_agents.py             Week 10's local triage, refund and specialist agents
    release_candidates.py         Week 12's candidates v2.1 to v2.4, each one deliberate change to v2
    tracing.py                    Week 13's span recorder: OpenTelemetry data model, OpenInference attributes, redaction
    governance.py                 Week 14's evaluation platform: tenants, roles, registry, redaction, audit chain, budgets
    course_checks.py              keeps notebooks and theory HTML in step with their sources
  datasets/
    build_datasets.py             how the world and the refund cases were made
    build_answer_cases.py         how the Week 5 answer cases were made
    build_tool_cases.py ...       builders for the Phase 3 case sets below
    world.json                    40 synthetic customers, 89 orders, as of 2026-03-15
    manifest.json                 dataset version, policy version, counts and hashes
    policies/                     refund-policy-2026-01.md, rules R1 to R6
    corpus/                       6 more help-centre documents, one superseded, one internal
    retrieval/                    50 policy queries with graded section labels (Weeks 4, 6)
    answers/                      24 answer cases with evidence and reference facts (Weeks 5, 6)
    tools/                        30 tool cases with target orders and expected ledger rows (Weeks 7 to 10)
    trajectories/                 38 trajectory cases (Week 8)
    conversations/                25 multi-turn scenarios with restart points (Week 9)
    faults/                       fault, handoff and poisoned-chunk cases (Week 10)
    development/                  73 cases, including Week 1's 30 (shared, so kept at the root)
    holdout/                      27 cases, used only for release decisions
  weeks/
    week-01-evaluation-basics/
      README.md                   week index
      theory/                     week-01-evaluation-basics-theory.md and .html
      handson/                    week-01-evaluation-basics-handson.md and .ipynb, lab.py, tests/
      dataset/                    cases.jsonl, README.md
    week-02-golden-datasets/      same three folders
    week-03-judges-and-human-calibration/   same three folders
    week-04-retrieval-evaluation/ ... week-16-distributed-evaluation-capstone/   same three folders
```

`shared/` holds only what more than one week uses. New agent versions will be added beside v1, not written over it. Every earlier lab then keeps producing the results its guide shows. The same applies to datasets: a corrected dataset gets a new version and manifest, and `refund-cases-v1` stays as it is.

## Data and labeling status

All customers, orders, payments and policies are synthetic. Case labels are computed from the refund policy's rules by `datasets/build_datasets.py`, and each scenario was written to test a stated outcome.

Week 3 ships two kinds of practice data that are not evidence. The judge responses are hand-written in the judge's output format to exercise the parser and report. They are not output from any model. The example review sheet is written by the course author and marked `example-not-human-review`, and the report prints a warning whenever it is used. A calibration result needs your own human labels and a live judge run.

Phase 2 adds three more limits, each stated in its guide:

- The concept-vector retriever is a hand-built stand-in for an embedding model, and its lexicon was written alongside the queries. Dense retrieval is measured only through it until the optional `dense-live` command runs.
- The retrieval and answer labels were written by one annotator, the course author, and nobody has reviewed them.
- Week 6's cost and latency are simulated from illustrative constants.

The optional live paths (the Week 3 judge, Week 4 embeddings, Week 5 Ragas) have been checked against the pinned packages but not run against a model.

Phase 3's agents are deterministic code standing in for a model. Their prompt-injection results describe those stand-ins, not any real model's susceptibility.

Phase 4 adds simulated evidence of three kinds, each labeled SIMULATED in its data and guide: Week 11's model-judged check is a seeded stand-in, Week 12's canary metrics are hand-written, and Week 13's traffic, latency and feedback come from a seeded generator. Week 12's thresholds are illustrative. The Week 11 CI workflow is an example that has never run on GitHub. Week 13's OpenTelemetry SDK export has been run locally with the in-memory exporter; no collector or hosted service has been used.

Phase 5 is simulated in the same way. Week 14's teams, people, budgets and costs are fictional, and its platform is an in-process prototype on one SQLite file with no real authentication. Week 15's passes and fails are drawn from seeded probabilities the author chose, and both of its review sheets are authored, so its kappa values test the method, not a judge. Week 16's workers run on a simulated clock with a scripted fault plan; its thread trial is a real measurement on one machine, not a production capacity estimate.
