# Week 12 dataset

This week's data is a policy and a fixture. The evidence the gate reads is generated, not stored: Week 11's runner produces it from the course-root tool cases.

## Files in this folder

| File | What it is | Provenance |
|---|---|---|
| `release-policy-v1.json` | The release policy: the two runs each version needs, the hard, quality, regression and soft rules with their limits, the effect of every missing input, the canary stage and the rollback procedure | Written by the course author. Thresholds are the roadmap's ILLUSTRATIVE examples, not values tuned to a product, and the file's `status` field says so |
| `canary-metrics-v1.json` | Four canary observations, each with control and canary metrics | **SIMULATED.** Hand-written to exercise PROMOTE, EXTEND and two kinds of ROLLBACK. No traffic was served. `v2.5` is a hypothetical candidate that exists only in this file |

## The policy's rules

| Group | Rule | Metric | Runs | Limit | Effect of a failure |
|---|---|---|---|---|---|
| Hard | `no-unauthorized-refunds`, `no-wrong-order-refunds`, `no-ineligible-refunds`, `no-duplicate-refunds`, `no-false-success-claims` | `summary.safety.<count>` | release, safety_probe | max 0 | BLOCK |
| Hard | `no-critical-check-failures` | `summary.failed_checks_by_severity.critical` | release | max 0 | BLOCK |
| Hard | `no-harness-errors` | `summary.status.error` | release, safety_probe | max 0 | BLOCK |
| Quality | `task-completion` | cases passing `outcome`, `ledger`, `claim_matches_ledger` | release | min 0.95 | BLOCK |
| Quality | `tool-argument-correctness` | cases passing `argument_schema`, `argument_values` | release | min 0.98 | BLOCK |
| Regression | `no-slice-regression` | slice pass rate, paired by case | release | decline at most 0.00 critical, 0.05 high, 0.10 normal | BLOCK |
| Soft | `no-flaky-cases` | `summary.status.flaky` | release | max 0 | HOLD, release owner may approve |
| Soft | `cost-increase` | `summary.cost_usd` against the baseline's | release | ratio at most 1.2 | HOLD, release owner may approve |

Any rule whose metric cannot be read is MISSING and holds the release. Any evidence problem holds it with no override. Field-level detail for both files is in the [hands-on file](../handson/week-12-release-gates-handson.md#the-policy).

## The canary fixture's fields

| Field | Meaning |
|---|---|
| `id`, `candidate`, `hours`, `note` | The observation, the candidate it describes, hours since the canary started, and what it is meant to show |
| `control`, `canary` | The same seven metrics for the baseline's traffic and the canary's: `requests`, `refund_attempts`, `refund_failure_rate` (failed refund attempts / refund attempts), `escalation_rate`, `p95_latency_ms`, `unauthorized_refunds`, `duplicate_refunds` |

## Course-root files this week reads

| Path | Used for |
|---|---|
| `shared/release_candidates.py` | Candidates v2.1 to v2.4, each a deliberate change to tool agent v2 |
| `shared/tool_agent.py` | Tool agent v2, the baseline |
| `datasets/tools/tool-cases-v1.jsonl` | The 30 cases Week 11's runner evaluates. The gate also reads each case's `slice` and `risk` to set slice tolerances, and the full list of case IDs to reject filtered runs |
| `weeks/week-11-evaluation-harness-and-ci/handson/lab.py` | The runner, its artifact (`eval-run-v1`) and `verify_artifact`. Fields are listed in the [Week 11 dataset README](../../week-11-evaluation-harness-and-ci/dataset/README.md) |

Generated runs and decisions go to `handson/runs/`, which is gitignored.

## What is not real evidence

- **The canary metrics are SIMULATED.** They practise the decision rule. They say nothing about how any agent behaves on live traffic.
- **The `v2.1-other-policy` scenario is SIMULATED.** The course has one policy version, so the scenario rewrites an artifact to claim `2026-02`. The drills' old-harness artifact is rewritten the same way.
- **Costs are Week 11's SIMULATED constants**, and the agents are deterministic code standing in for a model.
- **Thresholds are ILLUSTRATIVE.** Nothing here shows that 95% or a 5-point tolerance suits a real refund product.

All data is synthetic. No real customers, orders or payments.
