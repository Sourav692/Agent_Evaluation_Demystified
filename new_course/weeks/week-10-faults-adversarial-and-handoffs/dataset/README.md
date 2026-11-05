# Week 10 dataset

This week has no data of its own. Its cases live in the course-root `datasets/faults/` folder, beside the other shared case sets. `datasets/build_fault_cases.py` writes all three files. Rerun it after editing a case, then rerun the Week 10 tests.

| File | What it is |
|---|---|
| `datasets/faults/fault-cases-v1.jsonl` | 11 single-agent cases: timeouts before and after commit, two timeouts, a duplicate delivery, another customer's order, an instruction in the customer's message, four cases on a poisoned corpus and one control |
| `datasets/faults/handoff-cases-v1.jsonl` | 5 cases for the triage, refund agent and specialist flow, one of them with the specialist path down |
| `datasets/faults/poisoned-chunks-v1.jsonl` | 1 synthetic help-centre chunk carrying an instruction to the agent. Lab code adds it to the normal corpus with `ToolRuntime(chunks=...)` |
| `datasets/world.json` | Week 7's customers and orders, read through `shared/support_agent.load_world` |
| `datasets/policies/`, `datasets/corpus/` | The help-centre corpus, unchanged. The poisoned chunk is never written into it |

Fields in `fault-cases-v1.jsonl`:

| Field | Meaning |
|---|---|
| `case_id` | `f-001` to `f-011` |
| `fault` | `timeout_after_commit`, `timeout_before_commit`, `double_timeout`, `duplicate_delivery`, `unauthorized_order`, `direct_injection`, `poisoned_policy` or `none` |
| `customer_id`, `message` | The signed-in customer and their message |
| `target_order` | The order the message is about |
| `tool_faults` | Passed to `ToolRuntime(faults=...)`, for example `{"create_refund": ["timeout_after_commit"]}` |
| `redeliver` | `true`: every `create_refund` reaches the backend twice |
| `poisoned_corpus` | `true`: the run's corpus includes the poisoned chunk |
| `acceptable_outcomes`, `expected_refunds`, `expected_escalation` | What policy 2026-01 requires, whatever any injected text says |
| `label_source` | Who labeled the case |

`handoff-cases-v1.jsonl` has the same customer, message, target and expectation fields, plus `specialist_up`. The triage mode and the receiver are lab parameters, not case fields.

All of it is synthetic and author-labeled by one annotator. The poisoned text and the injected message use one obvious marker, `NOTE TO SUPPORT ASSISTANTS:`, chosen for teaching. They are not real attack payloads. No real customers, orders or payments.
