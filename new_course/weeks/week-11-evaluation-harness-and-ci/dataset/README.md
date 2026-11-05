# Week 11 dataset

This week has no data of its own. The runner executes two suites whose cases are shared with earlier weeks, so they live at the course root. What the week adds is an output: the run artifact.

## Inputs the runner reads

Every file below is pinned by its SHA-256 hash in `PINS` in `handson/lab.py`. A changed file stops the run with exit 3. For a folder, the hash covers every file's relative name and content.

| Path | Suite | What it is |
|---|---|---|
| `datasets/tools/tool-cases-v1.jsonl` | `tools` | Week 7's 30 tool cases in eight slices. Fields are listed in the [Week 7 dataset README](../../week-07-tools-and-side-effects/dataset/README.md) |
| `datasets/faults/fault-cases-v1.jsonl` | `faults` | Week 10's 11 fault cases. Fields are listed in the [Week 10 dataset README](../../week-10-faults-adversarial-and-handoffs/dataset/README.md) |
| `datasets/faults/poisoned-chunks-v1.jsonl` | `faults` | One synthetic poisoned help-centre chunk |
| `datasets/world.json` | both | 40 synthetic customers and 89 orders. Seeds every run's ledger |
| `datasets/policies/` | both | Refund policy 2026-01 |
| `datasets/corpus/` | both | The help-centre documents `search_policy` retrieves from |
| `datasets/manifest.json` | both | Not pinned. The runner copies its `dataset_version` and `policy_version` into every artifact |

The checks come unchanged from `weeks/week-07-tools-and-side-effects/handson/lab.py` and `weeks/week-10-faults-adversarial-and-handoffs/handson/lab.py`. The code hash in each artifact covers those files, the shared modules they run and this week's `lab.py`.

## The artifact the runner writes

Each `run` writes two files to its `--out` folder. Generated runs under `handson/runs/` are gitignored. Week 12's release gate reads them.

**`results.json`**, schema `eval-run-v1`:

| Field | Meaning |
|---|---|
| `schema_version` | `eval-run-v1` |
| `run_id` | `run-` plus 12 hex characters of SHA-256 over `config` without `workers`, and `versions` |
| `started_at` | UTC start time, `YYYY-MM-DDTHH:MM:SSZ`. Not part of the run ID |
| `config` | `suite`, `agent`, `backend`, `judge`, `seed`, `retries`, `budget_usd`, `workers` |
| `versions` | `case_set`, `data_sha256` (`{path: sha256}` for every input above that the suite reads), `dataset_version`, `policy_version`, `code_sha256` |
| `environment` | `python` and `platform`. Not part of the run ID |
| `expected_cases`, `completed_cases`, `complete`, `stop_reason` | Completeness. `complete` is true only when every case has a record |
| `summary` | `status` (`pass`, `fail`, `flaky`, `error` counts), `failed_checks_by_severity` (first attempts), `safety` (sums of the five counts below), `cache_hits`, `cost_usd` |
| `cases[]` | Per case: `case_id`, `slice`, `status`, `cached`, `cost_usd`, `safety`, `attempts[]` |

Each attempt holds `attempt`, `outcome`, `checks[]` (`check`, `passed`, `severity`, `reason`), `error`, `safety`, `fingerprint` and `cost_usd`. The five safety counts, read from the ledger rows the attempt wrote:

| Count | A refund row that... |
|---|---|
| `unauthorized_refunds` | is on an order owned by another customer |
| `wrong_order_refunds` | is on the customer's own order, but not the case's target order |
| `ineligible_refunds` | is on the target order, which policy 2026-01 does not allow refunding (window, final sale, over $500) |
| `duplicate_refunds` | is a second or later refund on the same order |
| `false_success_claims` | is missing: the agent claimed a refund and the ledger has none for that order |

**`checksums.json`**: `run_id` and `files: {"results.json": sha256}`, so a later job can prove the file is complete and unaltered.

## What is not real evidence

- **Costs are SIMULATED.** $0.0004 per tool call and $0.0010 per judge call are illustrative constants, not any provider's prices.
- **The `judge_reply_quality` check is SIMULATED.** It is a seeded random stand-in for a model judge. Its flip rates describe that stand-in, not any real model.
- **The agents are deterministic code** standing in for a model, as in Weeks 7 to 10.
- **The CI workflow example has not run on GitHub.** Only its structure is tested.

All data is synthetic. No real customers, orders or payments.
