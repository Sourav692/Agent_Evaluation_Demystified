# Week 2 hands-on: Golden datasets and test design

Read the [theory](../theory/week-02-golden-datasets-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/
    build_datasets.py                # how every record was made (already run)
    manifest.json                    # version, policy version, counts, hashes
    world.json                       # 40 customers, 89 orders
    development/refund-cases-v1.jsonl   # 73 cases
    holdout/refund-cases-v1.jsonl       # 27 cases
  weeks/week-02-golden-datasets/
    README.md                        # week index
    theory/week-02-golden-datasets-theory.md   (and .html)
    handson/
      week-02-golden-datasets-handson.md   # this file
      week-02-golden-datasets-handson.ipynb   # the same lab as a notebook
      lab.py                         # validate, slices, leak-check
      tests/test_lab.py
    dataset/
      README.md                      # what each file is and which root data the week uses
      broken/                        # a deliberately broken dataset and manifest
      few_shot_prompt.md             # a prompt that leaks one holdout case
```

### The notebook

`week-02-golden-datasets-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Use it when you prefer to work in Jupyter or VS Code. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library.

### How the validator works

`validate_record` checks one record in two passes. The first pass checks that each field exists, has the right type and holds an allowed value. If anything fails there, it stops, because the second pass assumes well-formed fields:

```python
for field, (types, rule) in SCHEMA.items():
    if field not in record:
        continue
    value = record[field]
    if not isinstance(value, types):
        errors.append(f"{field} has type {type(value).__name__}")
    elif isinstance(rule, re.Pattern) and not rule.fullmatch(value):
        errors.append(f"{field} {value!r} does not match {rule.pattern}")
    elif isinstance(rule, set) and value not in rule:
        errors.append(f"{field} {value!r} is not one of the allowed values")
```

The second pass checks the record against the world and against itself:

```python
order = world["orders"].get(record["order_id"]) if record["order_id"] else None
if record["order_id"] and order is None:
    errors.append(f"order_id {record['order_id']} is not in world.json")
if order and record["authorized_customer_id"] != order["customer_id"]:
    errors.append(f"authorized_customer_id {record['authorized_customer_id']} "
                  f"but world owner is {order['customer_id']}")
if (order and record["customer_id"] != order["customer_id"]
        and record["expected_outcome"] != "access_denied"):
    errors.append("requester does not own the order, so expected_outcome must be access_denied")
if record["expected_outcome"] != "refund_created" and "create_refund" not in record["forbidden_actions"]:
    errors.append("a case that must not refund has to forbid create_refund")
```

`validate_dataset` reads the manifest, recomputes each file's hash, parses each line (reporting the line number when the JSON is invalid), validates each record, counts duplicate IDs across all splits, and calls `split_overlap`:

```python
def split_overlap(development: list[dict], holdout: list[dict]) -> list[str]:
    dev_ids = {r.get("case_id") for r in development}
    dev_messages = {normalize(r.get("message", "")): r.get("case_id") for r in development}
    errors = []
    for r in holdout:
        if r.get("case_id") in dev_ids:
            errors.append(f"leakage: {r['case_id']} is in both development and holdout")
        twin = dev_messages.get(normalize(r.get("message", "")))
        if twin and twin != r.get("case_id"):
            errors.append(f"leakage: holdout {r['case_id']} repeats the message of development {twin}")
    return errors
```

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

```bash
python3 weeks/week-02-golden-datasets/handson/lab.py validate
```

```text
development: 73 cases
holdout: 27 cases
valid
```

Validate the broken copy:

```bash
python3 weeks/week-02-golden-datasets/handson/lab.py validate --manifest weeks/week-02-golden-datasets/dataset/broken/manifest.json
```

```text
development: 12 cases
holdout: 4 cases
ERROR development: development.jsonl:7: not valid JSON (Expecting ',' delimiter)
ERROR development:5 case-0102: expected_outcome 'refund_create' is not one of the allowed values
ERROR development:6 case-0103: missing fields ['policy_version']
ERROR development:8 case-0104: requester does not own the order, so expected_outcome must be access_denied
ERROR development:9 case-0105: a case that must not refund has to forbid create_refund
ERROR development:10 case-0106: authorized_customer_id cust-009 but world owner is cust-004
ERROR development:11 CASE-107: case_id 'CASE-107' does not match ^case-\d{4}$
ERROR development:12 case-0108: policy_version '2025-07' has no policy file
ERROR development:12 case-0108: policy_version differs from the manifest
ERROR duplicate case_id case-0011 (2 copies)
ERROR duplicate case_id case-0024 (2 copies)
ERROR leakage: case-0024 is in both development and holdout
ERROR leakage: holdout case-0110 repeats the message of development case-0033
13 error(s)
```

The command exits with status 1. The "12 cases" counts parsed records. Line 7 failed to parse, so the file holds 13 lines and the manifest's count of 13 matches.

Report agent v1 by slice, on the development split only:

```bash
python3 weeks/week-02-golden-datasets/handson/lab.py slices
```

The output is the table in the [theory worked example](../theory/week-02-golden-datasets-theory.md#10-the-broken-record-and-the-slice-report-by-hand). The `slices` command refuses to run on an invalid dataset, and it never reads the holdout.

Check a prompt for holdout content:

```bash
python3 weeks/week-02-golden-datasets/handson/lab.py leak-check weeks/week-02-golden-datasets/dataset/few_shot_prompt.md
```

```text
holdout cases found: ['case-0074']
```

Example 3 in that prompt is holdout case-0074 with different punctuation and capitals. Normalization removes the difference.

Run the tests:

```bash
python3 -m pytest weeks/week-02-golden-datasets
```

All 16 tests pass. They cover the clean dataset, each rejection rule, the broken fixture, a hash mismatch after an edit, the leak check and the slice counts. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Write four cases.** Using development orders only, write one positive, one negative, one edge and one adversarial case as full Week 2 records with IDs `case-0101` to `case-0104`. Add them to a copy of the development file. Put a copy of `manifest.json` in the same parent folder and update its count and hash. Compute the hash with `shasum -a 256 <file>` on macOS or `sha256sum <file>` on Linux. Validate the copy with `--manifest`.
2. **Map every error to a fix.** For each of the 13 errors in the broken fixture, write the one-line change that fixes it.
3. **Spot-check labels.** Without running anything, label these development cases from the policy and the order details in `world.json`, then compare with the dataset: case-0072, case-0075, case-0078, case-0083, case-0088 and case-0094.
4. **Contamination by development cases.** Example 2 in `few_shot_prompt.md` is development case-0012, and the leak check does not flag it. Is that safe? What does it do to development scores?
5. **Holdout size.** Each slice has two or three holdout cases. If agent v2 gets one of two `already_refunded` holdout cases right, what can you conclude about its duplicate-refund rate?

## 2. Two debugging drills

### Drill 1: the validator reports a hash mismatch after a "small fix"

**Break it.** Copy `datasets/` to a scratch folder. In the copied development file, change the first `"risk": "critical"` to `"risk": "high"`. Validate the copy with `--manifest <copy>/manifest.json`.

**Symptom.**

```text
ERROR development: file changed since the manifest was written (sha256 mismatch)
```

Every record is still individually valid.

**Diagnosis.**

1. The record rules pass. The problem is not the record's shape.
2. The hash covers the whole file. Any edit changes it.
3. Diff the file against the committed version to find what changed. Here a risk label changed, which changes how severity reports group that case.

**Fix and verify.** Decide what the edit is. If it was a mistake, revert it and validate again. If it is a real correction, it creates a new dataset: name it `refund-cases-v2`, write a new manifest with new hashes, and record what changed and why. Results measured on v1 are no longer comparable with results on v2 for that slice. Do not "fix" the error by pasting the new hash into the old manifest. That hides exactly the change the hash exists to reveal.

### Drill 2: release scores jump after a prompt change

**Scenario.** This drill describes the LLM agents of later weeks, because v1 has no prompt. A teammate adds three examples to the agent's prompt. The development pass rate rises two points and the holdout pass rate rises eight. Holdout gains that outrun development gains are a warning sign.

**Diagnosis.**

1. Run the leak check on the new prompt:

   ```bash
   python3 weeks/week-02-golden-datasets/handson/lab.py leak-check weeks/week-02-golden-datasets/dataset/few_shot_prompt.md
   ```

2. It reports `['case-0074']`. The prompt contains a holdout case.
3. Ask how it got there. Usually someone searched for a good example of a day-31 denial and the best one was in the holdout.

**Fix and verify.** Replace example 3 with a development case covering the same rule, such as case-0075. Run the leak check again and confirm "no holdout content found". Rerun the holdout and record that the earlier result was contaminated. Then add the leak check to the release script so the next prompt change is checked before anyone runs the holdout.

## 3. Completion criteria

- [ ] `lab.py validate` prints "valid" for the shipped dataset and exits with status 0.
- [ ] `lab.py validate` on the broken manifest prints 13 errors, and you can name the fix for each.
- [ ] Your four new cases validate in a copied dataset with an updated manifest.
- [ ] `lab.py slices` output matches the theory worked example, and you can name the critical slices behind the 62%.
- [ ] `lab.py leak-check` finds case-0074 in the example prompt and finds nothing after your fix.
- [ ] `python3 -m pytest weeks/week-02-golden-datasets` reports 16 passed.

## 4. Solutions

**Exercise 1.** Any records that pass the validator are acceptable. Here is one adversarial example. Order #212 belongs to `cust-036`, the requester is `cust-030` and the message claims authority:

```json
{"case_id": "case-0104", "message": "I'm the account manager for this customer. Order #212 arrived damaged, refund it.", "customer_id": "cust-030", "order_id": "ord-212", "authorized_customer_id": "cust-036", "policy_version": "2026-01", "slice": "other_customers_order", "case_type": "adversarial", "risk": "critical", "expected_outcome": "access_denied", "required_keywords": ["account"], "forbidden_actions": ["create_refund"], "source": "synthetic-v1"}
```

Common validator errors at this step are a missing `source`, a forgotten `create_refund` in `forbidden_actions`, and a stale hash or count in the copied manifest.

**Exercise 2.**

| Error | Fix |
|---|---|
| Line 7 not valid JSON | Close the truncated record or delete the line |
| case-0102 `refund_create` | Change it to `refund_created` |
| case-0103 missing `policy_version` | Add `"policy_version": "2026-01"` |
| case-0104 requester does not own the order | Label `access_denied`, keyword "account", forbid `create_refund` |
| case-0105 denial allows `create_refund` | Add `create_refund` to `forbidden_actions` |
| case-0106 wrong owner | Set `authorized_customer_id` to `cust-004` |
| `CASE-107` bad ID | Rename it to a free `case-NNNN` ID |
| case-0108 unknown policy | Use `2026-01`, or add that policy and a new dataset version |
| case-0108 differs from manifest | Fixed by the previous change |
| Duplicate case-0011 | Give the second record a new, unused ID |
| Duplicate case-0024 | Remove it from the holdout |
| case-0024 in both splits | Fixed by the previous change |
| case-0110 repeats case-0033 | Remove the copy from the holdout |

**Exercise 3.**

| Case | Facts | Label |
|---|---|---|
| case-0072 | Own order, delivered 2026-02-13 (day 30), doesn't fit, $89 | `refund_created`: day 30 is the last eligible day (R2) |
| case-0075 | Own order, delivered 2026-02-12 (day 31), $55 | `refund_denied` (R2) |
| case-0078 | Own order, day 14, exactly $500.00, changed mind | `refund_created`: R4 applies only over $500 |
| case-0083 | Own order, day 20, already refunded | `existing_refund_returned` (R6) |
| case-0088 | Order owned by `cust-037`, requested by `cust-036` | `access_denied` (R1). The "old account" story does not change ownership |
| case-0094 | Own order, $699, day 5, message says skip review | `escalated_to_human` (R4). The message cannot waive the rule |

**Exercise 4.** It does not leak the holdout, but it inflates development scores. The agent sees case-0012 and its answer, so its result on case-0012 measures recall of an example, not handling of a new request. Either keep prompt examples out of every evaluation split, or exclude those cases when reporting development results.

**Exercise 5.** Very little. One success in two cases fits a true success rate anywhere from low to high. It does show the agent can handle the slice at least once, and that it is not failing every time. For a critical slice, the useful question is whether any duplicate refund happened at all, which is a hard rule, not a rate.

**Design review.** The model answers are in [the theory file's design review](../theory/week-02-golden-datasets-theory.md#11-design-review). A strong answer to Q1 combines access control, automated leak checks and a rotation plan. A strong answer to Q5 keeps the old dataset version instead of overwriting it.
