# Week 7 dataset

This week has no data of its own. Its cases and backend are shared with Weeks 8 to 10, so they live at the course root:

| File | What it is |
|---|---|
| `datasets/tools/tool-cases-v1.jsonl` | 30 tool cases in eight slices: `eligible` (6), `two_orders` (4), `other_customer` (5), `expired` (4), `final_sale` (3), `high_value` (3), `already_refunded` (3), `missing_order` (2) |
| `datasets/build_tool_cases.py` | How every case was made. Messages are written by hand. Expectations follow policy 2026-01 |
| `datasets/world.json` | The customers and orders the tools read. Six orders already have a refund, which seeds the ledger |
| `shared/refund_store.py` | The SQLite ledger. Each run gets a fresh in-memory copy, so nothing is written to disk |

Each case has these fields:

| Field | Meaning |
|---|---|
| `case_id` | Stable ID, `t-001` to `t-030` |
| `message` | What the customer wrote |
| `customer_id` | The signed-in, verified customer |
| `slice`, `risk` | The condition tested, and the harm if it goes wrong |
| `target_order` | The order the customer means, or `null` when the message names none |
| `acceptable_outcomes` | The outcomes a correct agent may claim |
| `expected_refunds` | The only refunds the ledger may gain during the run |
| `expected_escalation` | The order that must be escalated, if any |
| `label_source` | `author-labeled, one annotator`: written by the course author and not reviewed by a second person |

All data is synthetic. No real customers, orders or payments.
