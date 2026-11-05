# Week 9 dataset

| File | What it is |
|---|---|
| `v2-transcripts.jsonl` | The golden transcripts: session agent v2's replies to every turn of the 25 scenarios, recorded word for word by `lab.py freeze`. Agent output, not labels. The exact-text comparison in `lab.py wording` reads them |

This week also reads data that later weeks share, so it lives at the course root:

| File | What it is |
|---|---|
| `datasets/conversations/conversations-v1.jsonl` | 25 conversation scenarios in five slices (restart, clarification, digression, isolation, combined), 86 turns, 10 restart points. Written by `datasets/build_conversations.py`. Never edit the JSONL by hand: edit the builder and rerun it |
| `datasets/world.json` | Customers and orders as of 2026-03-15, the same world as Weeks 1 to 8 |
| `datasets/policies/`, `datasets/corpus/` | The help-centre corpus that `search_policy` answers digressions from |

Each scenario has these fields:

| Field | Meaning |
|---|---|
| `scenario_id` | Stable ID, `conv-01` to `conv-25` |
| `slice` | `restart`, `clarification`, `digression`, `isolation` or `combined` |
| `description` | One line saying what the scenario varies |
| `sessions` | Every (customer, session) pair in the scenario. Two customers may share a session ID on purpose |
| `turns` | The turns in order, each with the fields below |
| `expected_refunds` | The refunds the ledger must hold at the end: order ID and amount. Nothing else may be stored |
| `expected_escalations` | Order IDs that must have been escalated to a specialist |
| `label_source` | `author-labeled, one annotator`: written by the course author and not reviewed by a second person |

Each turn has these fields:

| Field | Meaning |
|---|---|
| `customer_id` | The signed-in customer, from authentication |
| `session_id` | The session ID the customer's app sends |
| `message` | What the customer types |
| `restart_before` | `true` if the harness restarts the agent before this turn |
| `expect.outcome` | The outcomes accepted for this turn, such as `refund_offered` or `clarification_requested` |
| `expect.order_id` | The order the agent must have in focus after this turn, or `null` |

No field holds the expected reply text. Expectations follow refund policy 2026-01 and the confirm-before-refund flow in `shared/session_agent.py`.

All data is synthetic. No real customers, orders or payments.
