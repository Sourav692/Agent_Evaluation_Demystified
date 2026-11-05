# Week 14 dataset

Three files define the platform's tenants, their evaluators and one dataset with personal data. The other datasets the teams register are the course-root files below, read unchanged. `handson/lab.py` registers everything into an in-memory SQLite database on every run, so the files here are the only state.

| File | What it is |
|---|---|
| `tenants-v1.json` | The policy the platform enforces: three fictional teams with their runner, reserve per case and monthly budget; nine fictional principals, each with one tenant and one role; and the four roles as lists of permissions. Budgets and reserves are SIMULATED dollars, chosen so the scripted day ends with one budget denial |
| `evaluators-v1.json` | The three evaluators, each with its owner, its rules and the tenants it is shared with. `refund-safety` limits the five Week 11 safety counts to 0 and is shared with `refunds-agent`. Thresholds are illustrative, as in Week 12 |
| `escalation-queries-v1.jsonl` | 8 retrieval queries written as escalated tickets, with relevance labels for the help-centre corpus. They carry synthetic personal data on purpose, so redaction has something to remove |
| `datasets/retrieval/policy-queries-v1.jsonl` | Week 4's 50 policy queries: `support-rag/policy-queries` |
| `datasets/tools/tool-cases-v1.jsonl` | Week 7's 30 tool cases: `refunds-agent/tool-cases` |
| `datasets/faults/fault-cases-v1.jsonl` | Week 10's 11 fault cases: `trust-safety/fault-cases` |
| `datasets/world.json` | The synthetic customers. Their names are what identity-aware redaction masks |
| `datasets/policies/`, `datasets/corpus/` | The help-centre documents the retrieval runner searches, unchanged |

Fields in `escalation-queries-v1.jsonl`, the same as Week 4's query file:

| Field | Meaning |
|---|---|
| `query_id` | `e-001` to `e-008` |
| `query` | The ticket text. Six name the customer, four carry an `example.com` email, two a published test card number, one a typed customer ID |
| `slice` | `escalation` for all eight |
| `relevance` | Graded relevance per chunk ID, copied from the Week 4 query each ticket paraphrases |
| `label_source` | `author-labeled, one annotator` |

Fields in `tenants-v1.json`:

| Field | Meaning |
|---|---|
| `tenants.<id>.runner` | Which runner the platform calls for this tenant's runs: `retrieval`, `tools` or `faults` |
| `tenants.<id>.reserve_per_case_usd` | The SIMULATED cost reserved per case before a run is admitted |
| `tenants.<id>.monthly_budget_usd` | The SIMULATED budget that reservations and charges are checked against |
| `principals.<id>` | The principal's tenant (`*` for the platform auditor) and role |
| `roles.<role>` | The permissions the role grants, such as `dataset.read` or `evaluator.share` |

Everything here is synthetic or illustrative. The teams and principals are fictional. The customer names come from the synthetic `world.json`, the emails are built from them on `example.com`, a domain reserved for examples, and the card numbers are two published test numbers that no bank issues. No file here is evidence about a real organization's roles, budgets or data.
