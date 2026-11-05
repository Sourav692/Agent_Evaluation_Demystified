# Week 13 dataset

Two configuration files. Neither holds requests: `handson/lab.py` generates all 5,600 of them from `traffic-config-v1.json` with a seeded random generator, so the same file always gives the same traffic, traces and alerts. Change the seed or a rate, rerun the lab, and the hands-on file's pasted output no longer matches.

| File | What it is |
|---|---|
| `traffic-config-v1.json` | The SIMULATED traffic: seed 13, 400 requests a day for 14 days, the topic mix for normal days and for the day-4-to-6 clearance sale, how often a message carries a name and email or a card number, the gateway timeout rate, the SIMULATED feedback model, the two agent versions and the day-9 deploy |
| `online-policy-v1.json` | The online policy: four alerts with window, threshold, volume metric, minimum volume and severity; the rollback rule; the tail-sampling reasons and head rate; the salt for customer pseudonyms. Thresholds are illustrative, chosen against this replay's baseline |
| `datasets/world.json` | The course-root customers and orders, read through `shared/support_agent.load_world`. Requests are replayed against it as of 2026-03-15 |
| `datasets/policies/`, `datasets/corpus/` | The help-centre corpus that `search_policy` retrieves from, unchanged |

Fields in `traffic-config-v1.json`:

| Field | Meaning |
|---|---|
| `seed`, `days`, `requests_per_day` | The generator's seed and volume |
| `topic_mix` | Weights per message template, `baseline` and `clearance_sale` |
| `phases` | Which days use a mix other than `baseline` |
| `identity_in_message_rate`, `card_number_in_message_rate` | Share of messages starting `Hi, this is <name> (<email>).` and ending with a test card number |
| `gateway_timeout_rate` | Chance that any `create_refund` call times out, half before and half after the commit |
| `feedback_rate`, `thumbs_down_given_outcome` | Share of requests with feedback, and the chance of a thumbs-down for each claimed outcome |
| `versions`, `initial_version`, `deploys` | v2.2 (`stable_key`) and v2.3 (`no_retry`) from `shared/fault_agents.py`, and when v2.3 ships |

Everything here is synthetic. The names come from the synthetic `world.json`. The emails are built from them on `example.com`, a domain reserved for examples. The card numbers are two published test numbers that no bank issues. The feedback is a probability model written by the course author, not user data, and the thumbs-down rates are illustrative.
