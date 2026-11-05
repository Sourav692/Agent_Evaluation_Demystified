# Week 8 dataset

This week has no data of its own. It reads one case file at the course root, so Weeks 9 and 10 can reuse it:

| File | What it is |
|---|---|
| `datasets/trajectories/trajectory-cases-v1.jsonl` | 38 trajectory cases. tr-001 to tr-030 are Week 7's tool cases with a trajectory specification added. tr-031 to tr-038 are new messages in which the customer quotes an amount |
| `datasets/build_trajectory_cases.py` | Writes the file above. It runs tool agent v2 on the strict backend and refuses to write a reference path v2 does not follow |
| `datasets/tools/tool-cases-v1.jsonl` | Week 7's 30 tool cases, read by the builder |
| `datasets/world.json` | The synthetic customers and orders the backend serves |

Never edit the case file by hand. Change the builder and rerun it from `new_course/` with `python3 datasets/build_trajectory_cases.py`, then rerun this week's lab and tests.

Each case has these fields:

| Field | Meaning |
|---|---|
| `case_id` | Stable ID, `tr-001` to `tr-038` |
| `tool_case_id` | The Week 7 case it extends (`t-001` to `t-030`), or `null` for the eight new cases |
| `message`, `customer_id` | The customer's message and the signed-in, verified customer |
| `slice`, `risk` | Week 7's slices (`eligible`, `two_orders`, `other_customer`, `expired`, `final_sale`, `high_value`, `already_refunded`, `missing_order`) and their risk labels |
| `target_order` | The order the message is about, or `null` if it names no existing order |
| `acceptable_outcomes` | Outcomes the agent may claim |
| `expected_refunds`, `expected_escalation` | What the ledger and its events must hold after the run |
| `quotes_amount` | `true` when the message states the amount, as in "refund the $189.00" |
| `required_steps` | Calls that must appear and succeed on the named order, in any order |
| `allowed_mutations` | The only `create_refund` or `escalate_to_specialist` calls permitted. Any other attempted mutation is forbidden |
| `reference_trajectory` | v2's tool names for the case, kept for exact-match comparisons |
| `label_source` | `author-labeled, one annotator`: written by the course author and not reviewed by a second person |

The agents are in `shared/trajectory_agents.py` (variants) and `shared/tool_agent.py` (v1 and v2). The partial-credit weights in `lab.py` are illustrative.

All data is synthetic. No real customers, orders or payments.
