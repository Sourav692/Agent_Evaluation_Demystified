# Materials creation plan for the evaluation roadmap

Create a complete learning track from the [16-week Enterprise RAG and Agent Evaluation roadmap](enterprise-rag-agent-evaluation-roadmap.md). Use one customer-support refund agent throughout, starting with basic checks and ending with a simulated shared evaluation platform.

This document plans the work. Weekly lessons, labs, and supporting files remain to be created. The roadmap's 8–10 hours per week describes learner effort, not an estimate of authoring time.

## Learning outcomes

By the end of the track, learners should be able to:

- Build versioned evaluation cases and explain what each metric measures.
- Diagnose retrieval, answer, tool, conversation, and persisted-outcome failures separately.
- Compare agent versions using safety checks, scenario-level results, and uncertainty.
- Produce repeatable release decisions and investigate failures through traces.
- Demonstrate tenant isolation, worker recovery, quotas, and an auditable release decision in a local prototype.

Assume basic Python, JSON, and command-line knowledge. Add a short setup primer covering these prerequisites, retrieval-augmented generation (RAG), model calls, and agent tool calls. Explain advanced concepts when they first appear.

## Planned material structure

Keep Markdown as the authoring source. Each week has the same three folders: `theory/` with the theory file, `handson/` with the hands-on file, `lab.py` and tests, and `dataset/` with the week's synthetic data and a README on its provenance. The enterprise evaluation skill's Deliverable format section defines the layout. Each theory file also has a rendered HTML copy (`tools/build_html.py`), and each hands-on lab also comes as a notebook that runs the same code as `lab.py`.

The following tree describes planned files, not existing deliverables:

```text
new_course/
  README.md
  materials-creation-plan.md
  enterprise-rag-agent-evaluation-roadmap.md
  setup.md
  glossary.md
  coverage.md
  requirements-core.txt
  requirements-integrations.txt
  shared/
    schemas.py
    support_agent.py
    refund_store.py
    fixtures.py
  datasets/
    policies/
    development/
    holdout/
  weeks/
    week-01-evaluation-basics/
      README.md
      theory/
        week-01-evaluation-basics-theory.md
        week-01-evaluation-basics-theory.html
      handson/
        week-01-evaluation-basics-handson.md
        week-01-evaluation-basics-handson.ipynb
        lab.py
        tests/
      dataset/
        README.md
        cases.jsonl
    ...
    week-16-distributed-capstone/
  capstone/
    architecture.md
    decisions/
    runbook.md
    demo.md
```

Create shared modules only as repeated use emerges. Keep weekly fixtures and starting states reproducible so a learner can revisit an earlier week after the shared agent changes. Use explicit policy and case versions rather than silently replacing data.

The course README will list prerequisites, study order, weekly links, and exact run commands. `coverage.md` will map every roadmap concept to its lesson section, exercise, and completion evidence. Create links only when their targets exist.

## What every weekly guide contains

Follow the enterprise evaluation skill's guide template, adapting headings to the week's topic. Start with 3–5 measurable outcomes, prerequisites, and the agent's starting behavior. Introduce a concrete failure before explaining the concepts needed to diagnose it.

Use descriptive topic headings and short paragraphs. Define each new term before using it in code or formulas. Explain a concept's meaning, mechanism, use, and limits through the refund example. For metrics, include small numbers, the calculation, and an interpretation. Keep Staff-level design trade-offs after the basic explanation.

Each full guide includes:

1. Theory and a worked example with inspectable inputs and results.
2. A runnable lab with setup, full learning code, commands, and expected output.
3. Positive, negative, edge, and relevant adversarial cases.
4. Two debugging drills with symptoms, diagnosis, fixes, and verification.
5. Three to five design-review questions with short model answers.
6. Acceptance checks, an answer key, a compact memory card, and the next week's dependency.

Keep solutions within the guide so readers can attempt exercises before opening the answer section. Do not repeat the theory in the answer key or memory card. Label outputs as illustrative until their producing code has been run.

## Weekly creation sequence

Author the weeks in dependency order. Each week extends the previous working project and adds evidence for its learning outcomes.

### Phase 1: Evaluation foundations

#### Week 1: Evaluation lifecycle and basic metrics

Explain offline and online evaluation, deterministic and probabilistic checks, correctness and quality, precision, recall, F1, and failure categories. Show why keyword matching can pass an incorrect answer.

Build 30 labeled cases and checks for exact outcomes, required keywords, and forbidden actions. Deliver a small runner with per-case reasons. Verify that it detects a known wrong outcome and forbidden refund, and that learners can calculate a small confusion matrix by hand.

#### Week 2: Golden datasets and test design

Explain ground truth, scenario slices, positive and negative cases, adversarial cases, dataset versions, leakage, and training/development/test separation. A slice is a group of cases sharing a condition, such as an expired refund window.

Expand to 100 cases with stable IDs, expected outcomes, policy versions, risk labels, and authorized users. Deliver a schema validator and split manifest. Reject malformed records, duplicate IDs, and overlap between development and holdout sets. Keep holdout answers out of prompts and tuning examples.

#### Week 3: Model judges and human calibration

Explain rubrics, binary and ordinal scores, pairwise comparisons, judge bias, reference-based and reference-free grading, and agreement with human labels.

Deliver a judge prompt, structured evaluator, human-review sheet for 30 samples, and disagreement report. Use recorded judge responses for local parser exercises. Require real human labels for calibration claims. Demonstrate a fluent unsafe answer that receives a favorable quality score while failing a deterministic safety check.

### Phase 2: RAG evaluation

#### Week 4: Retrieval evaluation

Explain Precision@k, Recall@k, Hit Rate@k, mean reciprocal rank (MRR), and normalized discounted cumulative gain (nDCG). Cover relevance labels, chunk sizes, and metadata filters.

Prepare 50 policy queries and graded relevance labels. Deliver results at k=3 and k=5 with per-query and slice metrics. Use fixed ranked lists for hand-checked calculations, then provide a dense-versus-hybrid retrieval experiment. Label fixed rankings as fixtures. Complete and measure the real retrieval comparison before claiming that experiment is validated.

#### Week 5: Answer quality and evidence

Explain faithfulness, correctness, relevance, abstention, citation support, hallucination, and access-aware retrieval. Show how an answer can match retrieved text while using an outdated policy.

Build outdated, contradictory, missing, and restricted-evidence scenarios. Deliver custom checks and a Ragas integration exercise. Verify unsupported claims, wrong citations, access violations, and appropriate abstention separately. Keep local fixture results distinct from model-judged results.

#### Week 6: RAG regression comparisons

Explain query rewriting, reranking, hybrid search, retrieval drift, version comparisons, and quality/cost/latency trade-offs.

Compare baseline and candidate versions on the same cases. Deliver a scorecard and release recommendation that includes a slice regression hidden by the overall average. Identify whether retrieval or generation caused the change. Mark simulated cost and latency explicitly.

### Phase 3: Agent evaluation

#### Week 7: Tools and persisted side effects

Explain tool choice, argument schemas, tool responses, authentication, authorization, and state changes. Authentication establishes identity. Authorization decides what that identity may do.

Implement checks around `get_customer`, `get_order`, `search_policy`, and `create_refund`. Deliver tool evaluators and independent database read-back checks. Reject wrong-order refunds, unauthorized actions, and success messages without a stored refund.

#### Week 8: Trajectories and task completion

Explain exact and flexible trajectories, required and forbidden steps, trace grading, task success, efficiency, and partial credit.

Deliver separate trajectory and outcome checkers. Accept valid alternative tool orders, enforce authorization before mutation, and inspect final refund state. Demonstrate that partial credit cannot override a hard safety failure.

#### Week 9: Multi-turn state

Explain sessions, checkpoints, clarification, context carryover, long conversations, and cross-session leakage.

Create 25 replayable conversation scenarios and a restartable harness. Verify order continuity after restart, clarification behavior, and tenant isolation. Check meaningful state and outcomes without requiring exact response wording.

#### Week 10: Faults, adversarial inputs, and handoffs

Explain timeouts, retries, idempotency, prompt injection, malicious tool content, agent routing, handoffs, and partial failures. Idempotency prevents a retried request from creating another refund.

Deliver a fault-injection suite and severity report. Test timeout after commit, duplicate requests, unauthorized orders, poisoned policy text, and failed handoffs. Read back the ledger to verify that retrying produces one refund. Model agent handoffs locally before adding any external orchestration framework.

### Phase 4: Release and operations

#### Week 11: Repeatable evaluation harness

Explain reproducibility, version pins, parallel runs, caching, budgets, flaky results, and continuous integration and delivery (CI/CD).

Deliver a command-line runner, structured JSON results, and a course-scoped workflow example. Verify exit codes, artifact completeness, version metadata, and cache separation. A retry must preserve the original failure evidence. Keep live-model jobs opt-in.

#### Week 12: Release gates

Explain hard and soft gates, slice thresholds, paired comparisons, acceptance policies, canaries, rollback, and fail-open versus fail-closed behavior.

Deliver a machine-readable release policy and decision report. Exercise a passing candidate, a quality regression, an unauthorized refund, and missing evidence. Define how each missing or invalid input affects the verdict. Treat roadmap thresholds as illustrative until justified by risk and data.

#### Week 13: Tracing and online evaluation

Explain OpenTelemetry, OpenInference, spans, sampling, feedback, alerts, privacy, and drift. A span records one operation within a trace of the full request.

Deliver instrumented retrieval, model, and tool paths, a local trace-linked dashboard, and an operations runbook. Replay synthetic traffic to test sampling, redaction, alerts, and rollback triggers. Label replayed traffic as simulated. Add a verified tracing integration without requiring a hosted service for the core lab.

### Phase 5: Enterprise architecture

#### Week 14: Tenant governance

Explain tenancy, role-based access control (RBAC), dataset and evaluator registries, versioning, personal-data redaction, audit logs, and team-level attribution.

Deliver a local evaluation API prototype for three fictional teams. Test dataset and evaluator permissions, cross-tenant access denial, audit events, and per-team usage attribution. Enforce permissions in backend code.

#### Week 15: Measurement reliability

Explain judge calibration, human disagreement, repeated runs, confidence intervals, paired tests, sample-size limits, and segment drift.

Deliver a seeded stochastic experiment, a paired bootstrap comparison, and a reliability report. Explain bootstrap resampling before code. Show how a two-percentage-point improvement can remain inconclusive. Distinguish synthetic variation from measured model variation and preserve case pairing during resampling.

#### Week 16: Distributed evaluation capstone

Explain queues, worker pools, admission control, backpressure, fairness, quotas, cost limits, fault recovery, and service-level objectives (SLOs).

Deliver a local multi-worker prototype, architecture diagram, dashboard, two architecture decision records, runbook, and demo. Integrate evaluation results, release gates, traces, and tenant controls. Demonstrate worker failure recovery, bounded retries, budget enforcement, and protection against tenant starvation. Record unfinished runs explicitly. Distinguish prototype measurements from production capacity estimates.

## Project and execution boundaries

Use synthetic customers, orders, and policies. Enforce identity, authorization, eligibility, and idempotency in backend logic. Inspect stored records and ledger events independently of agent claims. Treat retrieved documents and model judges as untrusted inputs.

Start with Python 3.12+, JSONL fixtures, SQLite, and straightforward evaluators. Maintain a local path without credentials for every week. Add framework integrations alongside that path where the roadmap calls for them. A recorded response teaches evaluation mechanics but does not establish live model quality.

Before writing integration code, check official documentation and verify compatible versions in an isolated environment. Preserve the repository's `langgraph==1.2.11` pin and existing course requirements. Do not synchronize the root environment as part of course setup.

Document live-model commands, expected costs, and required credentials separately. Execute paid models, hosted services, or deployments only when explicitly requested. For unexecuted integrations, record the validation gap rather than marking the exercise complete.

## Authoring workflow and milestones

First create the course index, setup primer, glossary, and coverage matrix. Define case, trace, result, and refund-record schemas with the smallest fields needed for Week 1. Then complete Week 1 as the reference package and check its clarity, runtime, and reproducibility before expanding the pattern.

For each later week, map the roadmap concepts to lesson sections and exercises, write the smallest working experiment, and capture its results. Write the explanation around that evidence. Add drills, solutions, and design questions, then run technical and editorial review.

| Milestone | Materials complete | Evidence required before proceeding |
| --- | --- | --- |
| Course setup | Index, setup, glossary, coverage matrix, Week 1 | Fresh local setup and known failures detected |
| Foundations | Weeks 1–3 | Versioned 100-case dataset, split checks, judge workflow with honest labeling status |
| RAG | Weeks 4–6 | Hand-checked metrics, evidence failures, paired version scorecard |
| Agents | Weeks 7–10 | Independent side-effect checks, replayable sessions, retry and injection failures caught |
| Release | Weeks 11–13 | Repeatable runner, gate decisions, trace-linked alert and rollback exercise |
| Enterprise | Weeks 14–16 | Isolation tests, uncertainty report, worker recovery and complete capstone demo |

## Completion and review criteria

A week is complete when its roadmap concepts appear in the coverage matrix, its local lab runs from documented commands, and its deliberately broken cases fail for the stated reasons. Check code, fixtures, expected output, solutions, and acceptance criteria together. Do not use generated model labels as evidence of human review.

Run only the relevant course tests. Never run bare repository-root `pytest`, which may invoke paid evaluations. Keep generated databases, model outputs, credentials, and run artifacts out of version control. Retain small reviewed illustrative fixtures with clear provenance.

Apply the enterprise skill's writing standard and bundled no-ai-slop checklist. Check defined terms, descriptive headings, paragraph flow, factual support, internal links, and repeated explanations. Remove filler without dropping mechanisms, limits, or failure evidence.

Update the course index and coverage matrix as files are created. If material is later published under `docs/`, register it in the site builder and run the repository's applicable index and link checks. Keep the initial authoring work within `new_course`.

The first implementation task is the course setup and Week 1 reference package. Use its review findings to refine the remaining packages before writing Weeks 2–3.
