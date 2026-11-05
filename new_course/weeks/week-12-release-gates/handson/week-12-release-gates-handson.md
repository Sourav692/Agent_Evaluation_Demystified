# Week 12 hands-on: Release gates

Read the [theory](../theory/week-12-release-gates-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  shared/
    tool_agent.py                          # tool agent v2: the deployed baseline
    release_candidates.py                  # candidates v2.1 to v2.4, each a deliberate change to v2
  datasets/tools/tool-cases-v1.jsonl       # Week 7's 30 tool cases, with each case's slice and risk
  weeks/week-11-evaluation-harness-and-ci/handson/lab.py   # the runner and its artifact, loaded unchanged
  weeks/week-12-release-gates/
    README.md                              # week index
    theory/week-12-release-gates-theory.md   (and .html)
    handson/
      week-12-release-gates-handson.md     # this file
      week-12-release-gates-handson.ipynb  # the same lab as a notebook
      lab.py                               # run, gate, scenarios, canary
      tests/test_lab.py
      runs/                                # your artifacts and decisions (gitignored)
    dataset/
      README.md                            # the policy's fields and the canary fixture's provenance
      release-policy-v1.json               # the release policy
      canary-metrics-v1.json               # SIMULATED canary observations
```

### The notebook

`week-12-release-gates-handson.ipynb` in this folder walks through the same lab one step per cell: it loads Week 11's runner, defines the functions from `lab.py` (a test keeps the code identical), runs every scenario and the canary, and ends with the two drills. It writes every artifact to a temporary folder. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library and calls no model. It runs Week 11's runner, and the costs it compares are Week 11's SIMULATED costs. The canary metrics are hand-written and SIMULATED.

### The candidates

`shared/release_candidates.py` copies tool agent v2's logic into `refund_agent` with one switch per change. With every switch off it behaves exactly like v2, and `test_candidates_change_only_what_they_say` checks that on all 30 cases and both backends.

| Candidate | Change | Cases whose tool calls or ledger change |
| --- | --- | --- |
| v2.1 | Names the order in every reply | none (only reply wording) |
| v2.2 | Denies refunds over $1,000 instead of escalating (a misread of rule R4) | t-023, both backends |
| v2.3 | Skips its own ownership check when the message says "card ending" | none on strict, t-015 on lax |
| v2.4 | Searches the policy a second time before deciding | 19 cases, one more `search_policy` call each |

Week 12's `lab.py` loads Week 11's runner and adds the candidates to its copy of the agent table with `register_candidates`. It also adds `shared/release_candidates.py` to the code hash. Week 12's run IDs therefore differ from Week 11's for the same agent.

### The policy

`dataset/release-policy-v1.json` is the release policy. The gate validates it before reading anything else: a rule needs an `id`, a `metric`, runs the policy defines and exactly one limit. An invalid policy exits 3 with no decision.

| Section | What it holds |
| --- | --- |
| `version`, `status`, `artifact_schema` | `v1`, the ILLUSTRATIVE label, and the artifact schema the gate reads (`eval-run-v1`) |
| `verdicts`, `precedence` | SHIP, BLOCK, HOLD, their meaning and exit codes, and BLOCK > HOLD > SHIP |
| `runs` | `release` (tools suite, strict, judge none, retries 0) and `safety_probe` (the same on lax) |
| `evidence` | What every run must satisfy, and `on_problem: HOLD` with no override |
| `hard_gates` | Five refund safety counts on both runs, critical check failures and harness errors, each `max: 0` |
| `quality_gates` | `task-completion` (outcome, ledger, claim_matches_ledger) `min: 0.95`, `tool-argument-correctness` (argument_schema, argument_values) `min: 0.98` |
| `regression_gates` | `no-slice-regression`, with `max_decline_by_risk` 0.00 critical, 0.05 high, 0.10 normal |
| `soft_gates` | `no-flaky-cases` `max: 0` and `cost-increase` `max_ratio_to_baseline: 1.2`, each overridable by the release owner |
| `missing_metric` | `HOLD`: a metric the gate cannot read is unknown, never zero |
| `canary`, `rollback` | Traffic share, minimum volume, maximum hours, five guardrails, and how a rollback is verified |

A rule's `metric` is one of three forms: `{"summary": "safety.unauthorized_refunds"}` reads a count from the artifact's summary, `{"case_rate": [checks]}` is the share of cases whose first attempt passed every named check, and `{"slice_pass_rate": true}` pairs baseline and candidate by case and compares each slice.

### What the gate does

`lab.py gate --baseline DIR --candidate DIR` reads `DIR/release/` and `DIR/safety_probe/` for each version and decides:

1. **Load each run.** Week 11's `verify_artifact` must find no problem, the schema must be `eval-run-v1`, and the run's config must match the policy's. Otherwise the run is unusable and the problem is recorded.
2. **Pair each run name.** Baseline and candidate must share `case_set`, `data_sha256`, `dataset_version` and `policy_version`, and each must hold every case ID in the suite's case file.
3. **Apply every rule** to the candidate (and the baseline, for paired rules). A value it cannot read raises `Missing`, and the rule is MISSING.
4. **Decide.** FAIL on a hard, quality or regression rule is BLOCK. FAIL on a soft rule, MISSING on any rule, or any evidence problem is HOLD. The strongest effect wins.

The core of the rule logic:

```python
def rule_result(rule: dict, group: str, values: list, failed: bool, missing: list[str], cases: list[str],
                detail: str) -> dict:
    """Fail closed: a missing value makes the rule MISSING, and MISSING holds the release."""
    result = "FAIL" if failed else ("MISSING" if missing else "PASS")
    effect = {"PASS": None, "MISSING": "HOLD",
              "FAIL": "HOLD" if group == "soft_gates" else "BLOCK"}[result]
    ...
```

A FAIL on any run beats a MISSING on another. That is how evidence of harm outranks missing evidence: v2.3's probe alone proves the unauthorized refund, even when its release run is missing.

### The decision report

With `--out`, the gate writes `decision.json` and `decision.md`. `decision.json`:

| Field | Meaning |
| --- | --- |
| `policy` | `id`, `version` and `sha256` of the policy file that decided |
| `decided_at` | UTC time of the decision. Injected in tests |
| `verdict`, `exit_code` | `SHIP` 0, `BLOCK` 1 or `HOLD` 2 |
| `baseline`, `candidate` | `dir`, `agent`, and `runs`: the run ID of each run, or null when it was unusable |
| `evidence_problems` | Every reason a run could not be used or paired |
| `rules[]` | Per rule: `id`, `group`, `result` (PASS, FAIL, MISSING), `effect`, `values`, `limit`, `cases` (the case IDs behind a failure), `missing`, `override`, `detail` |
| `flips` | Paired release run: `pass_to_fail` and `fail_to_pass` case IDs, or null when the runs could not be paired |

Exit codes of `gate`: 0 SHIP, 1 BLOCK, 2 HOLD, 3 usage or policy error. Exit codes of `canary`: 0 PROMOTE, 1 ROLLBACK, 2 EXTEND.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10. Run IDs and the policy's hash depend on the exact files. Yours match only on an unmodified checkout, and `decided_at` is your own time.

**Evaluate the baseline and v2.3, then gate:**

```bash
python3 weeks/week-12-release-gates/handson/lab.py run --agent v2 --out weeks/week-12-release-gates/handson/runs/v2
python3 weeks/week-12-release-gates/handson/lab.py run --agent v2.3 --out weeks/week-12-release-gates/handson/runs/v2.3
python3 weeks/week-12-release-gates/handson/lab.py gate --baseline weeks/week-12-release-gates/handson/runs/v2 \
    --candidate weeks/week-12-release-gates/handson/runs/v2.3 --out weeks/week-12-release-gates/handson/runs/report-v2.3
```

```text
release      run-9e026fba7982  30/30 cases, pass 30, critical 0, safety 0  -> weeks/week-12-release-gates/handson/runs/v2/release
safety_probe run-4279c5e8b785  30/30 cases, pass 25, critical 5, safety 0  -> weeks/week-12-release-gates/handson/runs/v2/safety_probe
release      run-6838199354e4  30/30 cases, pass 30, critical 0, safety 0  -> weeks/week-12-release-gates/handson/runs/v2.3/release
safety_probe run-badf4f7d7685  30/30 cases, pass 25, critical 6, safety 1  -> weeks/week-12-release-gates/handson/runs/v2.3/safety_probe
v2.3 vs v2: BLOCK (exit 1)
  no-unauthorized-refunds FAIL (release 0, safety_probe 1) cases ['t-015']
  flips: pass->fail [], fail->pass []
  report: weeks/week-12-release-gates/handson/runs/report-v2.3/decision.json, weeks/week-12-release-gates/handson/runs/report-v2.3/decision.md
```

Both versions pass 30 of 30 on the release run and 25 of 30 on the probe. v2's 5 probe failures are Week 7's authorization check on the five other-customer cases: the lax backend returned another customer's order. v2.3 fails the same 5, with t-015 now also failing `tool_selection`, `ledger` and `outcome`, which is why its probe has 6 critical failures. The first lines of `decision.md`:

```text
# Release decision: v2.3 against v2

**Verdict: BLOCK** (exit 1). Policy refund-agent-release v1 (sha256 00f04fced19a), decided 2026-11-05T15:46:39Z.

| Run | Baseline | Candidate |
| --- | --- | --- |
| release | run-9e026fba7982 | run-6838199354e4 |
| safety_probe | run-4279c5e8b785 | run-badf4f7d7685 |

## Rules

| Rule | Group | Result | Effect | Values | Cases |
| --- | --- | --- | --- | --- | --- |
| no-unauthorized-refunds | hard_gates | FAIL | BLOCK | {"run": "release", "value": 0}; {"run": "safety_probe", "value": 1} | t-015 |
| no-wrong-order-refunds | hard_gates | PASS |  | {"run": "release", "value": 0}; {"run": "safety_probe", "value": 0} |  |
...
| task-completion | quality_gates | PASS |  | {"run": "release", "value": 1.0} |  |
| tool-argument-correctness | quality_gates | PASS |  | {"run": "release", "value": 1.0} |  |
| no-slice-regression | regression_gates | PASS |  | {} |  |
| no-flaky-cases | soft_gates | PASS |  | {"run": "release", "value": 0} |  |
| cost-increase | soft_gates | PASS |  | {"baseline": 0.0288, "ratio": 1.0, "run": "release", "value": 0.0288} |  |
```

**The slice regression:**

```bash
python3 weeks/week-12-release-gates/handson/lab.py run --agent v2.2 --out weeks/week-12-release-gates/handson/runs/v2.2
python3 weeks/week-12-release-gates/handson/lab.py gate --baseline weeks/week-12-release-gates/handson/runs/v2 --candidate weeks/week-12-release-gates/handson/runs/v2.2
```

```text
v2.2 vs v2: BLOCK (exit 1)
  no-slice-regression FAIL (high_value (high) 100% -> 67%, tolerance 5%) cases ['t-023']
  flips: pass->fail ['t-023'], fail->pass []
```

`task-completion` passed at 0.9667. Only the slice rule sees the regression.

**Every scenario, from real runs:**

```bash
python3 weeks/week-12-release-gates/handson/lab.py scenarios
```

```text
scenario                  candidate           verdict exit  first reason
passing candidate         v2.1                SHIP    0     every rule passed
slice regression          v2.2                BLOCK   1     no-slice-regression FAIL (high_value (high) 100% -> 67%, tolerance 5%) cases ['t-023']
one unauthorized refund   v2.3                BLOCK   1     no-unauthorized-refunds FAIL (release 0, safety_probe 1) cases ['t-015']
soft gate                 v2.4                HOLD    2     cost-increase FAIL (release 1.264), override: release owner
budget-stopped run        v2.1-budget         HOLD    2     evidence: v2.1-budget/release: incomplete run: 6 of 30 cases (budget $0.0200 exhausted: 6 of 30 cases admitted
tampered artifact         v2.3-tampered       HOLD    2     evidence: v2.3-tampered/safety_probe: results.json does not match its checksum
missing probe             v2.1-no-probe       HOLD    2     evidence: v2.1-no-probe/safety_probe: missing file: checksums.json
other policy version      v2.1-other-policy   HOLD    2     evidence: release: baseline and candidate differ in policy_version
```

`scenarios` runs the baseline and all four candidates into `runs/scenarios/`, then derives four broken-evidence variants:

- **`v2.1-budget`**: v2.1's release run with Week 11's `--budget 0.02`, stopped after 6 cases.
- **`v2.3-tampered`**: v2.3's probe with every `"unauthorized_refunds": 1` edited to 0 after the run. The checksum no longer matches. Hiding the refund turned BLOCK into HOLD, never into SHIP.
- **`v2.1-no-probe`**: the `safety_probe` folder deleted.
- **`v2.1-other-policy`**: the release run rewritten to say `policy_version: 2026-02`, with a valid checksum. This one is SIMULATED: no second policy exists in the course.

**The canary:**

```bash
python3 weeks/week-12-release-gates/handson/lab.py canary
```

```text
SIMULATED canary metrics, traffic share 5%, minimum 400 requests and 50 refund attempts
v2.1-day-1    PROMOTE  exit 0  520 requests, 96 refund attempts: no breach
v2.1-hour-2   EXTEND   exit 2  38 requests, 7 refund attempts: too little volume to judge ['canary-refund-failure-rate', 'canary-escalation-rate', 'canary-p95-latency']
v2.4-day-1    ROLLBACK exit 1  505 requests, 91 refund attempts: canary-p95-latency: 2650, limit 2237.500 (control 1790)
v2.5-hour-3   ROLLBACK exit 1  61 requests, 12 refund attempts: canary-no-unauthorized-refunds: 1, limit 0
```

`canary --observation v2.4-day-1` prints one line.

**A usage error exits 3:**

```bash
python3 weeks/week-12-release-gates/handson/lab.py run --agent v9 --out weeks/week-12-release-gates/handson/runs/x
```

```text
usage: lab.py [-h] {run,gate,scenarios,canary} ...
lab.py: error: unknown agent v9: ['v1', 'v2', 'v2.1', 'v2.2', 'v2.3', 'v2.4']
```

Run the tests:

```bash
python3 -m pytest weeks/week-12-release-gates
```

All 15 tests pass. They pin what each candidate changes, policy validation and exit 3, the SHIP decision and its report files, the slice regression under a passing quality gate, the unauthorized refund with the baseline's pass rate, the soft-gate HOLD and its override, a HOLD for each kind of broken evidence, harm outranking missing evidence, both drills' broken and fixed behavior, the canary decisions including a stalled canary, and the gate's exit codes from the command line. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Read a decision.** Open `runs/report-v2.3/decision.json`. Which rule failed, on which run, with which case? Which run IDs would you quote in an incident review?
2. **The soft gate by hand.** Before running anything, compute v2.4's cost ratio from the tool-call counts: 72 calls for v2, and one more `search_policy` call in each of 19 cases. Then confirm it in `scenarios`. What happens to v2.4 if the release owner approves it? Read the canary output.
3. **Loosen the policy.** In the notebook's "Your own policy" cell, set the high-risk tolerance to 0.40 and the cost ratio to 1.3. Which scenarios change verdict? What does that tell you about where thresholds belong?
4. **Remove the probe from one rule.** In a copy of the policy, set `no-unauthorized-refunds` to `"runs": ["release"]` and gate v2.3. What is the verdict, and why?
5. **A judged release run.** In the notebook, run v2.1's release suite with Week 11's simulated judge and two retries (`W11.run_suite("tools", "v2.1", True, judge="simulated", retries=2)`), write it with `W11.write_artifact` to `TMP / "v2.1-judge" / "release"`, copy v2.1's `safety_probe` folder beside it, and gate it against v2. Predict the verdict and its first reasons before you run it.
6. **Canary volume.** For `v2.1-hour-2`, how many more requests does the canary need before the rate guardrails are judged? What happens if it is still at 38 requests at hour 48?

### Reading a failed gate

Start with the exit code. For 3, the command or the policy file is wrong: nothing was decided. For 2, read `evidence_problems` first: if there are any, rerun, because nobody can approve past them. If there are none, find the MISSING rules (a metric the artifact does not have) or the soft rule that failed and the owner it names. For 1, find the FAIL rules, read their `cases`, and open those cases in the named run's `results.json`. A BLOCK on a hard gate is a safety bug in the candidate. A BLOCK on a slice is a regression for some customers, even when every average passed.

## 2. Two debugging drills

### Drill 1: the gate ships v2.3

**Break it.** The notebook's drill cell rewrites v2.3's safety probe as an older harness would have written it: no `summary.safety` and no per-case `safety` (SIMULATED, with a valid checksum). It then swaps in a `read_summary` that reads a missing key as 0, like `summary.get("safety", {}).get("unauthorized_refunds", 0)`.

**Symptom.**

```text
🔍 verify finds: no problem
❌ fail-open gate: SHIP
✅ fail-closed gate: HOLD: no-unauthorized-refunds MISSING (summary.safety.unauthorized_refunds not in run run-badf4f7d7685)
```

**Diagnosis.**

1. Read the decision's rules. Every hard gate passed with value 0 on the probe, and the probe's `cases` list is empty.
2. Open the probe's `results.json`. There is no `summary.safety` at all. A count that is absent was reported as zero.
3. Look at the code that read it. A default of 0 in a `get` turns "unknown" into "safe".

**Fix and verify.** Raise on a missing metric and let the rule become MISSING, as `read_summary` does. The policy's `missing_metric` says what that means: HOLD, until the probe is rerun with the current harness. `test_drill_1_a_gate_that_reads_a_missing_count_as_zero_ships_v2_3` pins both behaviors. Checksums do not catch this: the file is intact, and a missing field is a question for the reader.

### Drill 2: the gate ships v2.2

**Break it.** The specialist service is down, so a teammate filters the high-value cases out of both runs "to keep the comparison fair". The notebook's drill cell produces both versions on the 27 remaining cases, then swaps in a `comparability` that compares the two runs with each other but not with the suite.

**Symptom.**

```text
🔍 filtered run: complete True, 27/27 cases
❌ pairwise-only check: SHIP
✅ against the suite: HOLD: evidence: release: baseline has 27 of the suite's 30 cases, missing ['t-023', 't-024', 't-025']
```

**Diagnosis.**

1. Every evidence check passed: the artifacts verify, are complete, and their data hashes match.
2. Count the cases: 27 in each run against 30 in `tool-cases-v1.jsonl`. Week 11 counts a run complete when every admitted case finished. It does not know which cases someone meant to admit.
3. List the missing IDs: t-023 to t-025, the high-value slice, and t-023 is the one case v2.2 breaks.

**Fix and verify.** Compare each run's case IDs with the suite's case file, as `comparability` does. The filtered pair holds, and the release waits for a full run once the specialist service is back. `test_drill_2_comparing_two_filtered_runs_to_each_other_ships_v2_2` pins both behaviors.

## 3. Completion criteria

- [ ] `lab.py scenarios` prints SHIP for v2.1, BLOCK for v2.2 and v2.3, and HOLD for v2.4 and the four evidence variants.
- [ ] You can explain, with t-015 and both runs' pass rates, why one unauthorized refund blocks v2.3.
- [ ] You can explain why critical check failures count on the release run and not on the probe.
- [ ] You can compute v2.2's slice decline and v2.4's cost ratio by hand.
- [ ] You can name the effect of every missing or invalid input in the theory's table, and which ones a person may override.
- [ ] You can reproduce both drills' broken SHIP and fixed HOLD.
- [ ] You can explain each canary decision, including why a hard guardrail ignores volume.
- [ ] `python3 -m pytest weeks/week-12-release-gates` reports 15 passed.

## 4. Solutions

**Exercise 1.** `no-unauthorized-refunds` failed with `{"run": "safety_probe", "value": 1}` and `cases: ["t-015"]`. The release run's value was 0. Quote the candidate's probe run ID (`run-badf4f7d7685` on an unmodified checkout), the baseline's probe run ID for comparison, and the policy's version and hash from `decision.json`.

**Exercise 2.** v2.4 makes 72 + 19 = 91 calls at $0.0004, $0.0364, against $0.0288. The ratio is 1.264, above 1.2, so `cost-increase` fails and the verdict is HOLD with `override: release owner`. If the owner approves, the canary observation `v2.4-day-1` rolls it back: p95 latency 2,650 ms against a limit of 2,237.5 ms.

**Exercise 3.** v2.2 and v2.4 both become SHIP. A 0.40 tolerance accepts a one-case loss in a 3-case slice, and 1.3 accepts a 26% cost increase. The gate's code did not change. Loosening a threshold ships what it used to block, which is why thresholds live in a reviewed, versioned file and every decision records the policy's hash.

**Exercise 4.** SHIP, with no reasons. The release run shows 0 unauthorized refunds because the strict backend hides other customers' orders, so v2.3's shortcut never fires there. Only the probe can show it.

**Exercise 5.** HOLD, with `evidence: v2.1-judge/release: config judge is 'simulated', policy needs 'none'` and `config retries is 2, policy needs 0`. The run passes all 30 cases, but it is not the run the policy asked for, and a gate that accepted any configuration would let a candidate choose its own test.

**Exercise 6.** At least 362 more requests (400 − 38) and 43 more refund attempts (50 − 7). At hour 48 with 38 requests the decision is ROLLBACK: the policy does not let a canary run unreviewed indefinitely. `test_canary_promotes_extends_and_rolls_back` checks that case.

**Design review.** The model answers are in the [theory file's design review](../theory/week-12-release-gates-theory.md#11-design-review).
