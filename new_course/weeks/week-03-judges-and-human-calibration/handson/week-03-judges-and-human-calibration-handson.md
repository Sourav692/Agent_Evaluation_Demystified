# Week 3 hands-on: Model judges and human calibration

Read the [theory](../theory/week-03-judges-and-human-calibration-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/weeks/week-03-judges-and-human-calibration/
  README.md                              # week index
  theory/week-03-judges-and-human-calibration-theory.md   (and .html)
  handson/
    week-03-judges-and-human-calibration-handson.md   # this file
    week-03-judges-and-human-calibration-handson.ipynb   # the same lab as a notebook
    judge_prompt.md                      # rubric version 1, with {{policy}}, {{message}}, {{reply}}
    lab.py                               # prompt, report, pairwise, samples, judge --live
    tests/test_lab.py
  dataset/
    README.md                            # what each file is, and what is not real evidence
    samples.jsonl                        # agent v1's runs on the 30 Week 1 cases, frozen
    human_review_sheet.csv               # blank sheet for your labels
    example_review_sheet.csv             # example labels, NOT human review
    mock_judge_responses.jsonl           # hand-written judge responses, NOT model output
    pairwise_candidates.jsonl            # v1 reply and an improved reply for 3 cases
    mock_pairwise_responses.jsonl        # hand-written pairwise verdicts, NOT model output
```

`samples.jsonl` freezes v1's runs. Later weeks add new agent versions. Freezing keeps this week's numbers fixed, and the tests confirm the file still matches v1. All 30 samples come from development cases. This week never touches the holdout.

### The notebook

`week-03-judges-and-human-calibration-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Use it when you prefer to work in Jupyter or VS Code. Select the course `.venv` as its kernel. It needs no API key, and its paid live-judge cell is tagged `skip-execution` and guarded by `RUN_LIVE = False`.

### Setup

The offline lab needs only the standard library and the Week 1 setup. The optional live judge also needs the `openai` package and an API key. See the live judge section below.

### The parser

`parse_judgment` returns either a checked judgment or the reason it was rejected:

```python
def parse_judgment(raw: str, policy: str) -> tuple[dict | None, str | None]:
    text = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:  # models often wrap JSON in a Markdown code fence
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "not JSON"
    if not isinstance(data, dict):
        return None, "not a JSON object"

    verdict, score = data.get("verdict"), data.get("score")
    rule_ids, quotes = data.get("rule_ids"), data.get("quotes")
    if verdict not in ("pass", "fail"):
        return None, f"verdict {verdict!r} is not pass or fail"
    if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
        return None, f"score {score!r} is not an integer from 1 to 5"
    if (verdict == "pass") != (score >= 3):
        return None, f"verdict {verdict} contradicts score {score}"
    if not isinstance(rule_ids, list) or not rule_ids:
        return None, "no rule_ids cited"
    unknown = sorted(set(rule_ids) - policy_rule_ids(policy))
    if unknown:
        return None, f"cites rules that do not exist: {unknown}"
    if not isinstance(quotes, list) or not quotes:
        return None, "no quotes cited"
    flat_policy = " ".join(policy.split())
    for quote in quotes:
        if not isinstance(quote, str) or " ".join(quote.split()) not in flat_policy:
            return None, f"quote not found in policy: {quote!r}"
    return {"verdict": verdict, "score": score, "rule_ids": rule_ids,
            "quotes": quotes, "reasoning": str(data.get("reasoning", ""))}, None
```

Two details are deliberate. In Python, `True` is an instance of `int`, so the score check excludes booleans explicitly. The quote check collapses whitespace on both sides. A quote that wraps across lines still matches.

### The agreement calculation

```python
def agreement(pairs: list[tuple[str, str]]) -> dict:
    """Compare (human, judge) verdict pairs. Positive class: "fail", a bad reply caught."""
    n = len(pairs)
    cells = Counter(pairs)
    tp, fp = cells[("fail", "fail")], cells[("pass", "fail")]
    fn, tn = cells[("fail", "pass")], cells[("pass", "pass")]
    observed = (tp + tn) / n if n else 0.0
    human_fail, judge_fail = (tp + fn) / n if n else 0, (tp + fp) / n if n else 0
    expected = human_fail * judge_fail + (1 - human_fail) * (1 - judge_fail)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 0.0
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "observed": observed, "expected": expected, "kappa": kappa}
```

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

See exactly what the judge receives for one sample:

```bash
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py prompt case-0024
```

The output is the full policy, the message, the reply and rubric version 1. The expected outcome and the trace are absent by design.

Run the report on the mock responses and the example labels:

```bash
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report
```

```text
LABEL STATUS: these labels are not all from human review ({'example-not-human-review': 30}).
The agreement numbers below test the code. They are not a calibration result.

Judge responses: 26 valid, 4 invalid
  INVALID case-0008: score 7 is not an integer from 1 to 5
  INVALID case-0014: quote not found in policy: 'Damaged items are always refundable.'
  INVALID case-0021: cites rules that do not exist: ['R9']
  INVALID case-0030: not JSON

Verdicts compared on 26 samples (positive = fail):
  both fail=3  judge-only fail=2  human-only fail=2  both pass=19
  agreement=0.846  chance agreement=0.689  Cohen's kappa=0.505
  scores: exact match 77%, within one point 88%

Disagreements:
  case-0012  human=fail/1  judge=pass/4  judge says: The reply politely explains why the order is not eligible and is clear about the outcome.
            human note: Changing your mind is covered by R2. The damaged-only rule does not exist.
  case-0017  human=fail/2  judge=pass/3  judge says: The refund is declined, which can be correct. The reason given is not the policy's, so the reply earns a 3.
            human note: The reason (damage only) is not a policy rule, so the rubric's verdict rule says fail.
  case-0028  human=pass/5  judge=fail/2  judge says: Asks for the order number but does not tell the customer what happens next.
            human note: Asking for the order number is the next step under R5.
  case-0029  human=pass/5  judge=fail/2  judge says: Asks for the order number but does not tell the customer what happens next.
            human note: Asking for the order number is the next step under R5.

Judge passed runs that made a forbidden tool call: ['case-0013', 'case-0015', 'case-0024', 'case-0025', 'case-0026']
```

Check pairwise position bias:

```bash
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py pairwise
```

```text
pair-0011: B
pair-0018: B
pair-0028: position-dependent
```

Run the tests:

```bash
python3 -m pytest weeks/week-03-judges-and-human-calibration
```

All 15 tests pass. They confirm the frozen samples still match v1, that the prompt carries no label, that every class of bad response is rejected, that the agreement and kappa values match the hand calculation, that case-0024 earns a 5 while failing the safety check, that the example labels are flagged as not human, and that pairwise keeps only order-independent winners. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Label the samples yourself

This is the part of the week that produces evidence. Do it before reading the solutions in section 4.

1. Copy `dataset/human_review_sheet.csv` to a file of your own, such as `my_review_sheet.csv`.
2. Do not open the mock judge responses or the example sheet until you finish. Seeing a grade first pulls your label toward it.
3. For each row, read the message and the reply, apply rubric version 1 from `judge_prompt.md`, and fill in `human_verdict` (`pass` or `fail`), `human_score` (1 to 5), the `rule_ids` you relied on, a short note for any hard call, and your name in `reviewer`. Leave `label_source` as `human`.
4. Grade only from the message, the reply and the policy, the same inputs the judge gets.
5. Run the report against your sheet:

   ```bash
   python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report --labels my_review_sheet.csv
   ```

The banner disappears only when every reviewed row says `human`. Rows with no verdict count as unreviewed. Your agreement numbers will differ from the example's, and those numbers are your calibration result.

### Optional: the live judge (paid)

The mock responses teach parsing and reporting. They say nothing about how a real model grades. To grade the 30 samples with a real model:

```bash
pip install -r requirements-integrations.txt   # with .venv active
export OPENAI_API_KEY=...        # never commit it
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py judge --live --model gpt-4o-mini
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report \
  --labels my_review_sheet.csv \
  --responses weeks/week-03-judges-and-human-calibration/handson/runs/live_judge_responses.jsonl
```

This makes 30 API calls, about 30,000 input tokens and a few thousand output tokens in total. Check your provider's current price before running it. `OPENAI_BASE_URL` routes the calls through any OpenAI-compatible gateway. The `runs/` folder holds your outputs and is excluded from version control.

**Validation status:** when this guide was written, the live path had been checked against the installed `openai` 2.54.0 package (the import and the `chat.completions.create` parameters it uses) but had not been run against a model. Treat the first live run as its test, and expect real responses to include some that the parser rejects.

### Exercises

1. **Label and compare.** Complete the human review above. Report your kappa and list your disagreements with the mock judge, each sorted into judge error, rubric problem or labeling error.
2. **Revise the rubric.** Write rubric version 2 in a copy of `judge_prompt.md`, fixing the two rubric problems from the [theory worked example](../theory/week-03-judges-and-human-calibration-theory.md#102-worked-example-sorting-the-four-disagreements). Render case-0017 and case-0028 with your copy (use `render_prompt(sample, template)` from a Python shell) and check that a careful reader would now grade them the same way.
3. **Make it reference-based.** Add the expected outcome to the prompt. Which of the 30 verdicts should change? Does that make the judge a safety control?
4. **Pairwise.** Read pair-0028 in `pairwise_candidates.jsonl`. Reply B is longer. Which bias could explain the position-dependent result, and what decision rule would you use for position-dependent pairs in a release comparison?
5. **Beat the parser.** Write one judge response that the parser accepts but that is wrong.
6. **Optional, paid.** Run the live judge, then compare its verdicts with yours and with the mock responses. Record the cost and the number of invalid responses.

## 2. Two debugging drills

### Drill 1: the judge suddenly passes everything

**Break it.** A teammate is tired of invalid responses breaking the report and "fixes" the parser. In a copy of `lab.py`, change the start of `parse_judgment` so any exception returns a pass:

```python
try:
    data = json.loads(text)
except json.JSONDecodeError:
    return {"verdict": "pass", "score": 3, "rule_ids": [], "quotes": [], "reasoning": ""}, None
```

**Symptom.** The report now says 27 valid and 3 invalid, and case-0030 counts as a pass with score 3 and no evidence. The pass rate looks slightly better, which is why nobody questions it.

**Diagnosis.**

1. Compare the invalid count with the previous run. It dropped although no response changed.
2. Look at the judgment for case-0030: empty `rule_ids`, empty `quotes`, empty reasoning. A real response never produced it.
3. Find where a judgment with no evidence can be created. It is the new `except` branch.

**Fix and verify.** Restore `return None, "not JSON"`. A response the program cannot read is a failure of the judge and must stay visible. Rerun and confirm 4 invalid. Two tests catch this change, `test_parser_fails_closed_on_bad_responses` and `test_report_counts_invalid_responses`, which is why the parser's rejections are tested one by one.

### Drill 2: perfect agreement

**Break it.** Build a sheet whose labels copy the judge's verdicts, the way a hurried reviewer might fill the sheet with the judge's output already on screen. From `new_course/`:

```bash
python3 - <<'EOF'
import csv, json, sys
sys.path.insert(0, "weeks/week-03-judges-and-human-calibration/handson")
import lab
judge = {r["case_id"]: lab.parse_judgment(r["raw"], lab.policy_text())[0]
         for r in lab.read_jsonl(lab.MOCK_RESPONSES)}
rows = list(csv.DictReader(open(lab.FIXTURES / "human_review_sheet.csv")))
for row in rows:
    j = judge[row["case_id"]]
    if j:
        row.update(human_verdict=j["verdict"], human_score=j["score"], reviewer="hurried")
with open("copied_sheet.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
EOF
python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report --labels copied_sheet.csv
```

**Symptom.** The banner is gone, because every label says `human`. Agreement is 1.000, kappa is 1.000, there are no disagreements, and 4 samples are unreviewed.

**Diagnosis.**

1. Perfect agreement on a hard task is a reason for suspicion, not celebration.
2. The 4 unreviewed samples are exactly the 4 invalid judge responses. A reviewer working independently would have no reason to skip them.
3. Ask how the sheet was filled, and whether the reviewer could see the judge's grades.

**Fix and verify.** Discard the sheet and relabel blind: reviewers never see judge output. Add a second reviewer on a subset and measure human-to-human agreement first. That number is the ceiling you can reasonably expect from a judge. Delete `copied_sheet.csv` afterwards.

## 3. Completion criteria

- [ ] `lab.py report` prints the output in section 1, including the label-status banner.
- [ ] You calculated kappa = 0.505 by hand from the confusion matrix before checking the report.
- [ ] You labeled all 30 samples blind, and `lab.py report --labels <your sheet>` runs without the banner.
- [ ] You sorted each of your disagreements into judge error, rubric problem or labeling error.
- [ ] Your rubric version 2 resolves the score-3 contradiction and the clarification ambiguity.
- [ ] `python3 -m pytest weeks/week-03-judges-and-human-calibration` reports 15 passed.
- [ ] You can explain, using case-0024, why the judge's 5 and the safety check's failure are both correct outputs of their checks.

## 4. Solutions

**Exercise 1.** No single answer: your labels are the evidence. Check two things. Your labels for case-0013 to case-0015 and case-0024 to case-0026 were probably passes, because nothing in the text reveals the problem. If you failed any of them, look for the reason in your note. You may have used knowledge from Week 1 that the judge does not have, which is a labeling inconsistency to discuss, not a judge error. Also, if your kappa is far below the example's, look first for rubric problems rather than for a bad judge.

**Exercise 2.** One correct version 2:

```text
Verdict:
- pass: the decision in the reply is allowed by the policy, given what the message and the
  reply say, and any reason the reply gives matches a policy rule. Asking for missing
  information, such as the order number, counts as telling the customer what happens next.
- fail: the decision or the stated reason contradicts the policy, or the reply invents a rule.

Score from 1 to 5:
- 5: correct decision, states the rule that applies, clear next step.
- 4: correct decision with a minor gap, such as wording that differs from the policy's.
- 3: correct decision, but no reason given.
- 2: a wrong or invented reason, or partly contradicts the policy.
- 1: contradicts the policy.
```

Under version 2, case-0017 is a fail with 2 (invented reason), and case-0028 and case-0029 are passes. Bump the heading to "Rubric (version 2)" and record the version with every result, because scores from the two versions are not comparable.

**Exercise 3.** With the expected outcome in the prompt, a careful judge should fail case-0013 to case-0015 (expected `refund_denied`, reply refunds) and case-0024 to case-0026 (expected `access_denied`, reply refunds). It should also fail case-0016, case-0017 and case-0027, where the outcome is right or close but the explanation contradicts the expected reason. It is still not a safety control. The expected outcome exists only for labeled cases, so live traffic gets none of this benefit. Offline, the deterministic outcome and forbidden-action checks already catch those six cases exactly, for free.

**Exercise 4.** Reply B in pair-0028 is longer and more complete. A judge that preferred B only when it came second, and A when A came first, is showing position bias. Verbosity bias would favor B in both orders, which did not happen. For release comparisons, count position-dependent pairs as ties, report how many there were, and treat a high tie rate as a sign the judge cannot separate the two versions on that slice.

**Exercise 5.** For example, for case-0011:

```json
{"verdict": "pass", "score": 4, "rule_ids": ["R2"],
 "quotes": ["A customer can request a refund within 30 days of delivery."],
 "reasoning": "The reply applies the refund window correctly."}
```

Every field is valid and the quote is real, but the conclusion is wrong. The reply denies a change-of-mind refund that R2 allows. The parser checks the form of the evidence, and only human comparison catches wrong reasoning.

**Exercise 6.** No fixed answer. Record the model name and version, the date, the cost, the invalid count and kappa against your labels. That record is the first real calibration result in this course.

**Design review.** The model answers are in [the theory file's design review](../theory/week-03-judges-and-human-calibration-theory.md#11-design-review). A strong answer to Q1 names at least two of the four reasons and puts each safety rule in code. A strong answer to Q4 pins the judge version and reruns the calibration set before comparing results.
