# Week 14 hands-on: Multi-tenant governance

Read the [theory](../theory/week-14-multi-tenant-governance-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  shared/
    governance.py                         # the platform: principals, _authorize, registry, redaction, audit, usage
    tracing.py                            # Week 13's redaction patterns, reused for datasets and audit details
  datasets/
    retrieval/policy-queries-v1.jsonl     # support-rag's first dataset (Week 4)
    tools/tool-cases-v1.jsonl             # refunds-agent's dataset (Week 7)
    faults/fault-cases-v1.jsonl           # trust-safety's dataset (Week 10)
    world.json                            # customer names, masked by identity-aware redaction
  weeks/week-14-multi-tenant-governance/
    README.md                             # week index
    theory/week-14-multi-tenant-governance-theory.md   (and .html)
    handson/
      week-14-multi-tenant-governance-handson.md      # this file
      week-14-multi-tenant-governance-handson.ipynb   # the same lab as a notebook
      lab.py                              # runners, the scripted day, access matrix, probes, registry, redaction, audit
      tests/test_lab.py
      runs/week-14/platform.db            # written by the redaction command, git-ignored
    dataset/
      README.md                           # the files below and the shared data this week reads
      tenants-v1.json                     # teams, principals, roles, reserves and budgets
      evaluators-v1.json                  # the three teams' evaluators and the one grant
      escalation-queries-v1.jsonl         # 8 retrieval queries with synthetic personal data
```

### The notebook

`week-14-multi-tenant-governance-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. `shared/governance.py` and the lab use only the standard library, with `sqlite3` for storage. The lab loads Week 4's and Week 11's labs by path and runs them unchanged, so their datasets and shared modules must be in place.

The teams, people and budgets are fictional, and every cost is SIMULATED: Week 11's price per tool call, and $0.0002 per retrieval query. The clock is SIMULATED too: each reading is one minute after the last, starting 2026-03-16 09:00 UTC, so audit hashes come out the same on every run.

### The platform's API

`Platform` takes the caller's principal ID as the first argument of every method and nothing else about the caller. Every method resolves the resource it touches and passes the owning tenant to one function:

```python
def _authorize(self, actor: str, action: str, resource: str, owner: str | None) -> Principal:
    """Allow or deny `action` on `resource`, owned by tenant `owner` (None: it does not exist)."""
    p = self.principal(actor)
    if p is None:
        reason = "unknown_principal"
    elif action not in self.policy["roles"][p.role]:
        reason = "role"
    elif owner is None:
        reason = "missing"
    elif p.tenant not in ("*", owner) and not self._granted(resource, p.tenant, action):
        reason = "cross_tenant"
    else:
        self._audit(actor, p, action, resource, owner, "allow")
        return p
    self._audit(actor, p, action, resource, owner, "deny", reason)
    if reason == "role":
        raise Denied(f"{action} is not permitted for role {p.role}")
    raise Denied(PUBLIC_DENIAL)                    # missing and cross-tenant look the same
```

The rest of the module is short: `_register` and `_read` for the registry, `run_eval` for runs and budgets, `_audit` and `verify_audit` for the chain, and `usage`. Its docstring lists the public API.

### The three teams

| Tenant | Runner | Datasets | Evaluator it owns |
| --- | --- | --- | --- |
| `support-rag` | Week 4's `run_benchmark`, hybrid retriever, k = 5 | `policy-queries` (50), `escalation-queries` (8) | `retrieval-quality`: recall at 5 at least 0.8, no stale or restricted chunk |
| `refunds-agent` | Week 11's `run_suite("tools")`, strict backend by default | `tool-cases` (30) | `task-success`: pass rate at least 0.95 |
| `trust-safety` | Week 11's `run_suite("faults")` on the lax backend, as a safety probe | `fault-cases` (11) | `refund-safety`: the five Week 11 safety counts at most 0, shared with `refunds-agent` |

`SCRIPT` in `lab.py` is the day: two retrieval runs, refunds agent v1 and v2, the naive-retry and stable-key fault agents, and a refunds safety probe on the lax backend.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

**The day of work:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py demo
```

```text
Registered (SIMULATED platform, fictional teams):
  support-rag/policy-queries@v1
  support-rag/escalation-queries@v1
  refunds-agent/tool-cases@v1
  trust-safety/fault-cases@v1
  trust-safety/refund-safety@v1
  refunds-agent/task-success@v1
  support-rag/retrieval-quality@v1
run       actor             dataset                            args                           verdicts                               cost $
run-0001  rag.engineer      support-rag/policy-queries@v1      {}                             retrieval-quality PASS                 0.0100
run-0002  rag.engineer      support-rag/escalation-queries@v1  {}                             retrieval-quality PASS                 0.0016
run-0003  refunds.engineer  refunds-agent/tool-cases@v1        {"agent":"v1"}                 task-success FAIL, refund-safety FAIL  0.0392
run-0004  refunds.engineer  refunds-agent/tool-cases@v1        {"agent":"v2"}                 task-success PASS, refund-safety PASS  0.0288
run-0005  safety.engineer   trust-safety/fault-cases@v1        {"agent":"naive_retry"}        refund-safety FAIL                     0.0132
run-0006  safety.engineer   trust-safety/fault-cases@v1        {"agent":"stable_key"}         refund-safety PASS                     0.0132
-         refunds.engineer  refunds-agent/tool-cases@v1        {"agent":"v2","strict":false}  DENIED: budget exceeded for refunds-agent
```

Run-0003 fails `refund-safety` on v1's 3 wrong-order refunds and 11 false success claims. Run-0005 fails it on 3 duplicate refunds from naive retries. The refunds team uses trust and safety's evaluator by its full ref, and the last run is refused before it starts.

**Who can do what:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py access
```

```text
principal           1   2   3   4   5   6   7   8   9
rag.owner         yes yes yes yes  -   -   -  yes yes
rag.engineer      yes yes  -  yes  -   -   -   -   - 
rag.viewer        yes  -   -  yes  -   -   -   -   - 
refunds.owner     yes yes yes yes  -   -  yes yes yes
refunds.engineer  yes yes  -  yes  -   -  yes  -   - 
refunds.viewer    yes  -   -  yes  -   -  yes  -   - 
safety.owner      yes yes yes yes  -   -  yes yes yes
safety.engineer   yes yes  -  yes  -   -  yes  -   - 
platform.auditor   -   -   -   -   -   -   -  yes yes
  1. read own dataset
  2. write dataset
  3. write evaluator
  4. read own run
  5. read other team's dataset
  6. read other team's run
  7. use refund-safety
  8. read usage
  9. read audit
```

Every cell is a real call. Columns 5 and 6 are denied for everyone. Column 7 is allowed for the owner and the grantee, and for nobody in `support-rag`. The auditor reads usage and the log, and no data.

**Probing another team:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py probe
```

```text
refunds.engineer read_dataset       support-rag/escalation-queries@v1    -> not found or not permitted
refunds.engineer read_dataset       support-rag/escalation-queries       -> not found or not permitted
refunds.engineer read_dataset       support-rag/no-such-dataset@v1       -> not found or not permitted
refunds.engineer read_dataset       trust-safety/fault-cases@v1          -> not found or not permitted
refunds.engineer read_run           run-0001                             -> not found or not permitted
refunds.engineer read_run           run-0099                             -> not found or not permitted
refunds.engineer read_evaluator     support-rag/retrieval-quality@v1     -> not found or not permitted
refunds.engineer register_evaluator refund-safety                        -> evaluator.write is not permitted for role engineer
rag.owner's audit view: 4 denied events on support-rag resources
  seq  47 2026-03-16T09:59:00Z refunds.engineer dataset.read dataset:support-rag/escalation-queries@v1 reason=cross_tenant
  seq  48 2026-03-16T10:00:00Z refunds.engineer dataset.read dataset:support-rag/escalation-queries@v1 reason=cross_tenant
  seq  51 2026-03-16T10:03:00Z refunds.engineer run.read run:run-0001 reason=cross_tenant
  seq  53 2026-03-16T10:05:00Z refunds.engineer evaluator.read evaluator:support-rag/retrieval-quality@v1 reason=cross_tenant
```

The request without a version resolves to `@v1` in the log, because the platform resolves a ref before it decides.

**The registry:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py registry
```

```text
register tool-cases                  -> refunds-agent/tool-cases@v1
register the same 30 cases again     -> refunds-agent/tool-cases@v1
register with t-023 risk changed     -> refunds-agent/tool-cases@v2
read tool-cases@v1, t-023 risk       -> high
UPDATE tool-cases v1 in the database -> refused: registry entries are immutable: register a new version
read after a direct edit             -> refused: refunds-agent/tool-cases@v1 does not match its recorded sha256 cea3a4cc2952
```

The last two lines bypass the API. The first is stopped by the SQLite trigger. For the second, the lab drops the trigger, as someone with the database file could, and replaces v1 with 29 cases. The read recomputes the hash and refuses.

**Redaction:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py redaction
```

```text
where             emails  card numbers  customer IDs  names
raw upload             4             2             1      6
patterns only          0             0             0      6
database file          0             0            41      0
customer IDs in the database file: 41, 41 of them in the structured customer_id field the runner replays
escalation-queries recall@5: raw 0.8125, as stored 0.8125
wrote weeks/week-14-multi-tenant-governance/handson/runs/week-14/platform.db
```

"database file" scans the bytes of the SQLite file after the whole day: datasets, run records and the audit log. The 41 customer IDs are the synthetic `customer_id` fields of the tool and fault cases, which the runners need to replay each case.

**The audit log:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py audit
```

```text
end of day: head seq 46, hash 7420d10b8b881b26..., kept outside the database as the anchor
platform.auditor reads 47 events (the read itself is event 47):
  allow  -                  46
  deny   budget             1
verify: chain intact
after deleting seq 46: ['seq 47: expected seq 46, events are missing', 'seq 47: prev does not match the hash before it']
after rewriting the chain, without the anchor: chain intact
after rewriting the chain, with the anchor:    ['anchor seq 46: hash differs from the one stored outside the database']
a fresh day with only its newest event, seq 46, deleted: without the anchor chain intact, with it ['anchor seq 46: hash differs from the one stored outside the database']
```

The day writes 46 events: 4 dataset writes and 4 registrations, 3 evaluator writes and 3 registrations, 1 share, 7 run requests with their 7 dataset reads and 10 evaluator reads, 6 completed runs and 1 budget denial.

**Usage and attribution:**

```bash
python3 weeks/week-14-multi-tenant-governance/handson/lab.py usage
```

```text
tenant         runs cases   cost $  budget $   left $
support-rag       2    58   0.0116      0.05   0.0384
refunds-agent     2    60   0.0680      0.15   0.0820
trust-safety      2    22   0.0264      0.10   0.0736
denied: refunds.engineer eval.admit at 2026-03-16T09:58:00Z: spent 0.0680 + estimate 0.0900 > 0.15
```

`trust-safety` paid only for its own two runs, although the refunds team ran its evaluator twice.

Run the tests:

```bash
python3 -m pytest weeks/week-14-multi-tenant-governance
```

All 17 tests pass. They pin the day's runs, verdicts and the budget denial; the tenant and role coming from the policy, including an unknown principal; the access matrix; the identical answers to cross-tenant probes and their true reasons in the log; a grant that allows use and not change; registry versions, the trigger and the hash check; the hashes pinned in run records; a missing metric failing its rule; redaction measured on the database file; who can read which audit events; the chain against a deletion, a rewrite and a truncation; cost attribution; and Drill 1's leak. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Predict the grant.** Before running `access`, write down which of the nine principals can use `trust-safety/refund-safety@v1`. Then run it and explain each row.
2. **Share with the wrong team.** In the notebook's "your own cases" cell, have `safety.owner` share `refund-safety` with `support-rag`, then run `policy-queries` with both `retrieval-quality` and `refund-safety`. Predict each verdict first.
3. **The shadow evaluator.** On a fresh platform, have `refunds.owner` register an evaluator named `refund-safety` with no rules, then run tool agent v1 with the evaluator ref `refund-safety`, and again with `trust-safety/refund-safety`. Compare the verdicts and the hashes in the two run records.
4. **Price the reservation.** Set the refunds team's `reserve_per_case_usd` to 0.0014, a little above v1's measured $0.0392 / 30 cases, and rerun the day. Is the safety probe admitted? What do its two verdicts say?
5. **Who saw the probe.** After `probe`, list the denied events visible to `refunds.owner`, to `safety.owner` and to `platform.auditor`. Explain each difference.

### Reading a failed check

When a test about access fails, print the audit events of the call first: the decision, the reason and the owner tell you which branch of `_authorize` ran. A wrong `owner` means the ref resolved in the wrong namespace, so check `_resolve`. A wrong `reason` with the right owner means the role table or a grant is not what you expected, so check `tenants-v1.json` and the `grants` table. For registry failures, compare the stored `sha256` with `sha256_json` of what you registered: redaction changes free text before hashing, so the hash is over the redacted records.

## 2. Two debugging drills

### Drill 1: the API that trusted the caller's tenant

**Break it.** `read_run_trusting_caller(platform, actor, tenant, run_id)` in `lab.py` is the shared script from the theory's section 2. It checks that the caller's role may read runs and that the run belongs to the tenant the caller named.

**Symptom.** `read_run_trusting_caller(platform, "refunds.engineer", "support-rag", "run-0001")` returns the support team's run record: the dataset ref, its hash, the metrics and the verdicts. `platform.audit("platform.auditor")` has no event for the read.

**Diagnosis.**

1. Find where the tenant came from. The function compares the run's tenant with the `tenant` argument, which the caller chose.
2. Find where the decision was logged. Nowhere: the function reads the database directly, so `_audit` never runs.
3. Ask what else uses the same pattern. Any method that accepts a tenant, a team or an owner as a parameter has the same hole.

**Fix and verify.** Use `platform.read_run(actor, run_id)`, which reads the tenant from the principal. It raises `Denied: not found or not permitted` and writes a `cross_tenant` event that the support team's owner can read. `test_drill_1_trusting_the_callers_tenant_leaks_another_teams_run` checks both functions.

### Drill 2: the audit log that verified after tampering

**Symptom.** The refunds team's budget denial at seq 46 is gone from the log, and `platform.verify_audit()` returns no problems.

**Diagnosis.**

1. Count the events. There are 46, and the last is the auditor's read. The day wrote 46 events before that read, so one is missing.
2. Ask what the chain proves. Each hash covers the one before it. Someone deleted seq 46 with `delete_event`, then renumbered the later events and recomputed every hash from seq 46 on with `rewrite_chain`. Every link is valid, because every link was rewritten.
3. Compare with something outside the database. The anchor saved at the end of the day says seq 46 had hash `7420d10b…`. The rewritten seq 46 does not.

**Fix and verify.** Verify with the anchor: `platform.verify_audit(anchor)` reports `anchor seq 46: hash differs from the one stored outside the database`. Prevention is to store the head somewhere the platform's operators cannot rewrite, at least once per release decision, and to restrict who can reach the database file. `test_the_chain_catches_a_deletion_and_only_the_anchor_catches_a_rewrite` and `test_deleting_the_newest_event_is_invisible_to_the_chain_alone` pin both halves.

## 3. Completion criteria

- [ ] `lab.py demo` shows six completed runs and the refunds safety probe denied on budget, and you can say why run-0003 and run-0005 fail `refund-safety`.
- [ ] `lab.py access` shows columns 5 and 6 denied for every principal, and you can explain column 7 from the grant.
- [ ] `lab.py probe` shows seven identical answers, and you can say which two of those probes are `missing` in the log and who can see them.
- [ ] `lab.py registry` shows identical content keeping `@v1`, changed content making `@v2`, and both kinds of direct edit refused.
- [ ] `lab.py redaction` shows 0 emails, card numbers and names in the database file, and you can explain the 41 customer IDs.
- [ ] `lab.py audit` shows the deletion caught by the chain and the rewrite caught only by the anchor.
- [ ] You can explain from `lab.py usage` who paid for the refunds team's use of `refund-safety`.
- [ ] `python3 -m pytest weeks/week-14-multi-tenant-governance` reports 17 passed.

## 4. Solutions

**Exercise 1.** Five principals: `refunds.owner`, `refunds.engineer` and `refunds.viewer` through the grant, and `safety.owner` and `safety.engineer` because their tenant owns it. All three roles have `evaluator.read`, so even the refunds viewer can read it. The three `support-rag` principals are denied with the public message, and the auditor is denied for its role, which has no `evaluator.read`.

**Exercise 2.** `retrieval-quality` passes (recall 0.9033, no stale hits) and `refund-safety` fails with all five rules `MISSING`: a retrieval run produces no refund counts. The run costs support-rag $0.0100. A grant can make a check available to a team it does not apply to, and failing closed on missing metrics is what keeps that from turning into a silent pass.

**Exercise 3.** The short ref resolves in the caller's own namespace, so `refund-safety` means `refunds-agent/refund-safety@v1` (hash `da506c8a9c8a…`). With no rules it returns PASS for v1, which made 3 wrong-order refunds. The full ref `trust-safety/refund-safety` gives FAIL with hash `7628b1484f6b…`. The run records differ only in the evaluator ref and hash, which is why a release gate must check both.

**Exercise 4.** Yes. The reservation is 30 × $0.0014 = $0.042, and $0.068 + $0.042 = $0.110 fits under $0.15. Run-0007 costs $0.0288. `refund-safety` passes: v2 stores no bad refund even on the lax backend. `task-success` fails at 0.8333, because on the lax backend Week 7's authorization check fails v2 on the five other-customer cases. As in Week 12, quality rules belong to the release run and safety rules to the probe. The refunds team has $0.0532 left.

**Exercise 5.** `refunds.owner` sees 9 denied events: the budget denial and all 8 probes, because their own engineer made them, including the 2 `missing` ones. `safety.owner` sees 1, the read of `trust-safety/fault-cases@v1`. `platform.auditor` sees all 9. `rag.owner` sees the 4 on support RAG's resources, shown in the `probe` output.

**Design review.** The model answers are in the [theory file's design review](../theory/week-14-multi-tenant-governance-theory.md#12-design-review).
