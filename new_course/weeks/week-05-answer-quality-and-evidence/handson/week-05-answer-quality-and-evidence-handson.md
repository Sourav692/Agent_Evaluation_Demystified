# Week 5 hands-on: Answer quality and evidence

Read the [theory](../theory/week-05-answer-quality-and-evidence-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/
    answers/answer-cases-v1.jsonl         # 24 cases: question, evidence, reference facts
    build_answer_cases.py                 # how every case was made
  shared/
    answerer.py                           # answer writer v1, extractive, three deliberate bugs
    retrieval.py                          # Week 4's corpus and retrievers
  weeks/week-05-answer-quality-and-evidence/
    README.md                             # week index
    theory/week-05-answer-quality-and-evidence-theory.md   (and .html)
    handson/
      week-05-answer-quality-and-evidence-handson.md   # this file
      week-05-answer-quality-and-evidence-handson.ipynb   # the same lab as a notebook
      lab.py                              # seven checks, the report, the Ragas comparison
      tests/test_lab.py
    dataset/
      README.md                           # what each file is
```

The answer cases live at the course root because Week 6 reuses them.

### The notebook

`week-05-answer-quality-and-evidence-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key, and its paid Ragas cell is tagged `skip-execution` and guarded by `RUN_LIVE = False`.

### Setup

Setup is the same as Week 1. The lab uses only the standard library.

### What is in a case

```json
{"case_id": "a-009", "question": "How long do I have to ask for a refund?", "slice": "outdated", "retrieved": ["refund-policy-2025-06#R2", "refund-policy-2026-01#R2", "payments-policy-2026-01#P2"], "expected_behavior": "answer", "must_include": ["30 days"], "must_not_include": ["60 days"], "gold_sections": ["refund-policy-2026-01#R2"], "reference_answer": "Within 30 days of delivery.", "label_source": "author-labeled, one annotator"}
```

`retrieved` fixes the evidence the writer gets. A case can then fail on the writer alone. The `normal` cases take Week 4's filtered hybrid top 3. The other slices use evidence written by hand to reproduce one problem each.

### The writer

Writer v1 scores every sentence in the evidence by shared words and concepts with the question, and quotes the best two:

```python
def answer_v1(question: str, chunks: list[Chunk], max_sentences: int = 2) -> Answer:
    scored = [(overlap(question, s), rank, s, c.chunk_id)
              for rank, c in enumerate(chunks) for s in split_sentences(c)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    picked = [t for t in scored[:max_sentences] if t[0] >= 1.5]
    if not picked:
        # Bug 2: no abstention. A stock sentence, cited to whatever came first.
        first = chunks[0].chunk_id if chunks else None
        return Answer(FALLBACK_V1, [(FALLBACK_V1, first)], writer="v1")
    sentences = [(s, cid) for _score, _rank, s, cid in picked]
    return Answer(" ".join(s for s, _cid in sentences), sentences, writer="v1")
```

### The checks

Each check takes the case, the evidence and the answer. Three of the seven:

```python
def check_faithfulness(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """Every answer sentence must appear in some chunk the writer was given."""
    evidence = " ".join(norm(c.text) for c in chunks)
    unsupported = [s for s, _cid in answer.sentences if norm(s) not in evidence]
    if answer.abstained:
        return CheckResult("faithfulness", True, "abstained: nothing to support")
    reason = "every sentence is in the evidence" if not unsupported else f"unsupported: {unsupported}"
    return CheckResult("faithfulness", not unsupported, reason)


def check_correctness(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    text = norm(answer.text)
    required = case["must_include"] if case["expected_behavior"] == "answer" else []
    missing = [f for f in required if norm(f) not in text]
    present = [f for f in case["must_not_include"] if norm(f) in text]
    ok = not missing and not present
    reason = "required facts present" if ok else f"missing {missing}, forbidden {present}"
    return CheckResult("correctness", ok, reason)


def check_restricted_source(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """No sentence may come from an internal document. This is the access check."""
    by_id = {c.chunk_id: c for c in chunks}
    leaked = [cid for cid in answer.citations() if cid in by_id and by_id[cid].audience != "public"]
    return CheckResult("restricted_source", not leaked,
                       "no internal sources" if not leaked else f"quotes internal {leaked}")
```

The other four are citation support, relevance (cites a gold section), abstention and stale source.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

The report with each case's fixed evidence:

```bash
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report
```

```text
Writer v1, fixed evidence from each case:
slice (cases)           faith     cite  correct    relev  abstain    stale restrict    all
normal (8)               8/8      8/8      8/8      8/8      8/8      8/8      8/8    8/8
outdated (4)             4/4      4/4      0/4      4/4      4/4      0/4      4/4    0/4
contradictory (4)        4/4      4/4      3/4      4/4      4/4      4/4      4/4    3/4
missing (4)              0/4      0/4      4/4      4/4      0/4      4/4      4/4    0/4
restricted (4)           4/4      4/4      0/4      4/4      3/4      4/4      0/4    0/4
overall (24)            20/24    20/24    15/24    24/24    19/24    20/24    20/24  11/24

Critical failures (internal text in an answer): ['a-021', 'a-022', 'a-023', 'a-024']
Faithful to the evidence but incorrect: ['a-009', 'a-010', 'a-011', 'a-012', 'a-016', 'a-021', 'a-022', 'a-023', 'a-024']
```

The same cases with evidence from a filtered hybrid search:

```bash
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report --retrieval filtered
```

```text
Writer v1, evidence from a filtered hybrid search, top 3:
slice (cases)           faith     cite  correct    relev  abstain    stale restrict    all
normal (8)               8/8      8/8      8/8      8/8      8/8      8/8      8/8    8/8
outdated (4)             4/4      4/4      2/4      2/4      4/4      4/4      4/4    2/4
contradictory (4)        4/4      4/4      2/4      4/4      4/4      4/4      4/4    2/4
missing (4)              0/4      0/4      4/4      4/4      0/4      4/4      4/4    0/4
restricted (4)           4/4      4/4      4/4      4/4      3/4      4/4      4/4    3/4
overall (24)            20/24    20/24    20/24    22/24    19/24    24/24    24/24  15/24

Critical failures (internal text in an answer): []
Faithful to the evidence but incorrect: ['a-009', 'a-010', 'a-013', 'a-016']
```

One case in full:

```bash
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py case a-009
```

```text
a-009 (outdated): How long do I have to ask for a refund?
evidence: ['refund-policy-2025-06#R2', 'refund-policy-2026-01#R2', 'payments-policy-2026-01#P2']
  answer: A customer can request a refund within 60 days of delivery.  [refund-policy-2025-06#R2]
  answer: A customer can request a refund within 30 days of delivery.  [refund-policy-2026-01#R2]
reference: Within 30 days of delivery.
  PASS  faithfulness       [major] every sentence is in the evidence
  PASS  citation_support   [major] every citation supports its sentence
  FAIL  correctness        [major] missing [], forbidden ['60 days']
  PASS  relevance          [minor] cites a gold section
  PASS  abstention         [major] answered as expected
  FAIL  stale_source       [major] cites superseded ['refund-policy-2025-06#R2']
  PASS  restricted_source  [critical] no internal sources
```

```bash
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py case a-017
```

```text
a-017 (missing): Do you price-match other shops?
evidence: ['payments-policy-2026-01#P3', 'exchanges-policy-2026-01#E2', 'shipping-policy-2026-01#S1']
  answer: Refunds are available within 30 days of delivery.  [payments-policy-2026-01#P3]
reference: The help centre does not cover price matching. Pass the question to a specialist.
  FAIL  faithfulness       [major] unsupported: ['Refunds are available within 30 days of delivery.']
  FAIL  citation_support   [major] citations that do not support: ['payments-policy-2026-01#P3']
  PASS  correctness        [major] required facts present
  PASS  relevance          [minor] abstain case: no gold section
  FAIL  abstention         [major] answered when it should abstain
  PASS  stale_source       [major] no superseded sources
  PASS  restricted_source  [critical] no internal sources
```

Run the tests:

```bash
python3 -m pytest weeks/week-05-answer-quality-and-evidence
```

All 12 tests pass. They check the case set, the normal slice, the faithful-but-wrong outdated answer, the unsupported fallback, the critical internal leak, what the filter fixes and what it cannot, and a swapped-citation answer. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Optional: Ragas, model-judged (paid)

```bash
pip install -r requirements-integrations.txt   # with .venv active
export OPENAI_API_KEY=...                       # never commit it
python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py ragas --live --model gpt-4o-mini
```

It scores the same 24 answers with Ragas faithfulness, answer relevancy, context precision and context recall, and prints them beside the local faithfulness and correctness results, in columns labeled `local:` and `ragas:`. Expect on the order of 150 to 200 judge calls plus a few embeddings calls. That estimate comes from how each metric works, not from a measured run. Check your provider's prices first.

`requirements-integrations.txt` pins `openai` to 2.54.0, not 3.x, because Ragas 0.4.3 depends on `instructor`, which caps `openai` below 3.0. The file explains the other pins, which come from course 03.

**Validation status:** on 2026-11-05 the pin set was installed in an isolated Python 3.12 environment, `import ragas` succeeded, and the four metrics' `ascore()` keywords and `llm_factory` matched the code above. The command has not been run against a model. Its scores are unverified until it has, and they will vary between runs.

### Exercises

1. **Predict a filtered failure.** Before running it, predict how `case a-013 --retrieval filtered` fails, then check.
2. **Write two cases.** Write one `missing` case and one `restricted` case as full records, with evidence chosen from the corpus, and run them through `run_cases(cases=[...])` in a Python shell or the notebook.
3. **Make the writer abstain.** In the notebook's "your writer" cell, change the fallback so the writer abstains with `ABSTAIN_TEXT` when no sentence scores 1.5 or more. Which checks change on the missing slice?
4. **Explain a-016.** "Do I get store credit or a refund to my card?" passes faithfulness and fails correctness. Read the trace and say why.
5. **Classify every failure.** For each failing case, compare fixed and filtered results and label the cause retrieval, generation or both.

### Reading a failed check

Read faithfulness and correctness together before anything else. Faithful and incorrect points at the evidence. Unfaithful points at the writer. Then read relevance: a relevance failure means the gold section was not in the evidence, which is a retrieval problem. A restricted-source failure is critical whatever the other checks say.

## 2. Two debugging drills

### Drill 1: the citations point at the wrong rule

**Break it.** Take case a-001's answer and swap its two citations, so each sentence is attributed to the other chunk. The notebook's drill cell does this.

**Symptom.** Faithfulness still passes: both sentences are in the evidence. Citation support fails with "citations that do not support: ['payments-policy-2026-01#P2', 'payments-policy-2026-01#P1']".

**Diagnosis.**

1. Faithfulness checks the evidence as one pool. It cannot see which chunk a sentence was attributed to.
2. For each sentence, look up its cited chunk and search that chunk alone.
3. Each sentence is in the other chunk. The writer kept the right sentences and paired them with the wrong IDs, a typical off-by-one in code that zips sentences and sources.

**Fix and verify.** Carry the chunk ID with each sentence from the moment it is selected, as `answer_v1` does with `(sentence, chunk_id)` pairs, instead of rebuilding citations from positions afterwards. The test `test_citation_check_catches_a_sentence_cited_to_the_wrong_chunk` guards the check.

### Drill 2: a correct answer fails correctness

**Break it.** Give the checks an answer to case a-001 that says "Card refunds appear within 3-5 business days." The notebook's drill cell builds it.

**Symptom.** Correctness fails with "missing ['3 to 5 business days']". The answer is right.

**Diagnosis.**

1. Read the reason literally: the required phrase is "3 to 5 business days".
2. The answer says "3-5". Same fact, different format.
3. Phrase matching tests wording, the same weakness as Week 1's keyword check.

**Fix and verify.** Either normalize the formats the policy uses (ranges, currency, "30-day" and "30 days") before matching, or list accepted alternatives for each required fact. Rerun and confirm the answer passes, then confirm a genuinely wrong range such as "5 to 7 business days" still fails. If answers are paraphrased heavily, move correctness to a judge and calibrate it.

## 3. Completion criteria

- [ ] `lab.py report` and `lab.py report --retrieval filtered` match section 1.
- [ ] You can name a faithful but incorrect case and explain which check catches it.
- [ ] You can explain why the missing slice stays at 0 with either evidence.
- [ ] Your two new cases run, and you predicted their results first.
- [ ] Your abstaining writer passes abstention on the missing slice.
- [ ] `python3 -m pytest weeks/week-05-answer-quality-and-evidence` reports 12 passed.

## 4. Solutions

**Exercise 1.** The filtered search returns S3, S1 and R2. The writer quotes S3's 7-day sentence and then S1's delivery-time sentence, which scores higher than R2's for this question. The answer lacks "30 days", and correctness fails: "missing ['30 days']". With fixed evidence (S3, R2, S1) the same writer passes. The order of the evidence changed the answer.

**Exercise 2.** Any records with the case fields work. A restricted example:

```json
{"case_id": "a-101", "question": "How many refunds can I ask for before you get suspicious?", "slice": "restricted", "retrieved": ["refund-escalation-playbook-2026-01#I2", "refund-policy-2026-01#R6", "payments-policy-2026-01#P1"], "expected_behavior": "abstain", "must_include": [], "must_not_include": ["three refunds", "Flag the account"], "gold_sections": [], "reference_answer": "The help centre does not cover this. Pass the question to a specialist.", "label_source": "author-labeled, one annotator"}
```

V1 quotes I2's fraud rule and fails restricted source, correctness and abstention.

**Exercise 3.** With abstention, the four missing cases pass every check in both modes, because no sentence in their evidence scores 1.5. a-021 still fails abstention with filtered evidence: the lost-parcel sentence from S2 scores above the threshold, so the writer answers a compensation question with a lost-parcel rule. A score threshold tells weak matches from strong ones, not relevant evidence from evidence that only looks relevant. No normal case abstains: their best sentences all score above 1.5.

**Exercise 4.** The writer picked E2's store-credit sentence and P1's second sentence, "Support cannot send a refund to a different card or account." The required fact "original payment method" is in P1's first sentence, which scored lower. Both sentences are in the evidence, and faithfulness passes. The required fact is missing, and correctness fails. Choosing two sentences by word overlap misses the one that carries the answer.

**Exercise 5.**

| Case | Cause |
| --- | --- |
| a-009, a-010 | Retrieval: the outdated rule first, or, filtered, no current rule at all |
| a-011, a-012 | Retrieval: the outdated rule. Filtering fixes them |
| a-013 | Retrieval order: passes with fixed evidence, fails filtered |
| a-016 | Generation: fails with both evidence sets on the same sentence choice |
| a-017 to a-020 | Generation: no abstention |
| a-021 | Both: retrieval leaked internal text, and generation does not abstain |
| a-022 to a-024 | Retrieval: internal text in the evidence. Filtering fixes them |

**Design review.** The model answers are in the [theory file's design review](../theory/week-05-answer-quality-and-evidence-theory.md#11-design-review).
