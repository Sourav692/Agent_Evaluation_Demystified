# Week 6 hands-on: RAG regression comparisons

Read the [theory](../theory/week-06-rag-regression-comparisons-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  shared/
    rag_pipeline.py                       # versions v1, v2, v2.1, rewriting, reranking, SIMULATED cost/latency
    answerer.py                           # writers v1 and v2
    retrieval.py                          # Week 4's corpus and retrievers
  weeks/week-06-rag-regression-comparisons/
    README.md                             # week index
    theory/week-06-rag-regression-comparisons-theory.md   (and .html)
    handson/
      week-06-rag-regression-comparisons-handson.md   # this file
      week-06-rag-regression-comparisons-handson.ipynb   # the same lab as a notebook
      lab.py                              # scorecard, slices, paired, attribute, ablate, decide
      tests/test_lab.py
    dataset/
      README.md                           # the shared data this week reads
```

The lab reuses Week 4's metrics and Week 5's checks unchanged. It loads their `lab.py` files with `load_week_lab`, so a change there changes Week 6's numbers too.

### The notebook

`week-06-rag-regression-comparisons-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library.

### The versions

```python
V1 = PipelineConfig("v1", retriever="bm25", filtered=False, rewrite=False, rerank=False, k=3, writer="v1")
# The candidate. Its abstention threshold was raised to 3.0 to stop guessed answers.
V2 = PipelineConfig("v2", retriever="hybrid", filtered=True, rewrite=True, rerank=True, k=3,
                    writer="v2", min_score=3.0)
# The same candidate with the threshold Week 6's investigation recommends.
V2_1 = PipelineConfig("v2.1", retriever="hybrid", filtered=True, rewrite=True, rerank=True, k=3,
                      writer="v2", min_score=2.0)
```

Cost and latency come from `Pipeline.run` in `shared/rag_pipeline.py`. Tokens are words × 1.3. Latency adds fixed step delays (BM25 20 ms, hybrid 45 ms, rewriting 15 ms, reranking 60 ms) to per-token time. Every one of these constants is illustrative.

### The gold-context swap and the release rules

```python
def attribute(version: str) -> list[dict]:
    pipeline = Pipeline(VERSIONS[version], CHUNKS)
    out = []
    for row in answer_rows(version):
        if row["passed"]:
            continue
        case = row["case"]
        gold = [BY_ID[s] for s in case["gold_sections"]]
        swapped = pipeline.run(case["question"], evidence=gold)
        results = [check(case, gold, swapped.answer) for check in W5.CHECKS]
        cause = "retrieval" if all(r.passed for r in results) else "generation"
        out.append({"id": row["id"], "slice": row["slice"], "cause": cause,
                    "failed": [r.check for r in row["results"] if not r.passed],
                    "failed_with_gold": [r.check for r in results if not r.passed]})
    return out


POLICY = {
    "max_critical_failures": 0,         # internal text in an answer
    "max_slice_answer_drop": 0,         # passing answer cases lost on any slice
    "max_slice_recall_drop": 0.05,      # Recall@3 lost on any retrieval slice
    "max_p95_latency_increase": 0.20,   # simulated p95 at most 20% above the baseline's
}
```

`decide` applies `POLICY` and blocks the candidate when any rule fails.

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py scorecard --candidate v2
```

```text
metric                                          v1        v2
Retrieval Recall@3                           0.710     0.823
Retrieval MRR                                0.643     0.843
Retrieval nDCG@3                             0.616     0.791
Filter violations (150 slots)                   35         0
Answer cases passing all checks (24)            11        18
Critical failures                                5         0
Answers abstained                                0         8
SIMULATED cost per 1,000 answers ($)         0.107     0.096
SIMULATED p50 latency (ms)                     401       394
SIMULATED p95 latency (ms)                     615       649
```

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py slices --candidate v2
```

```text
kind      slice                       n       v1       v2    delta
answers   normal                      8        7        6       -1  <- regression
answers   outdated                    4        0        3       +3
answers   contradictory               4        3        3       +0
answers   missing                     4        0        4       +4
answers   restricted                  4        1        2       +1
retrieval exact_term                  8    0.875    0.875   +0.000
retrieval paraphrase                 10    0.350    0.700   +0.350
retrieval direct                     16    0.917    0.917   +0.000
retrieval outdated_trap               6    0.583    0.833   +0.250
retrieval restricted_trap             5    0.900    0.900   +0.000
retrieval multi_section               5    0.467    0.600   +0.133
```

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py paired --candidate v2
```

```text
Answer cases (v1 -> v2): 9 improved, 2 regressed
  regressed: ['a-002', 'a-023']
Retrieval queries, nDCG@3: 21 improved, 4 regressed
  regressed: ['q-011', 'q-021', 'q-030', 'q-046']
```

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py attribute --version v2
```

```text
Gold-context swap for v2's failing answer cases:
  a-001 (normal): generation failed ['correctness', 'relevance'], with gold evidence ['correctness', 'relevance', 'abstention']
  a-002 (normal): generation failed ['correctness', 'relevance', 'abstention'], with gold evidence ['correctness', 'relevance', 'abstention']
  a-009 (outdated): generation failed ['correctness', 'relevance', 'abstention'], with gold evidence ['correctness', 'relevance', 'abstention']
  a-016 (contradictory): generation failed ['correctness'], with gold evidence ['correctness']
  a-022 (restricted): generation failed ['correctness'], with gold evidence ['correctness']
  a-023 (restricted): generation failed ['correctness', 'relevance', 'abstention'], with gold evidence ['correctness', 'relevance', 'abstention']
```

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py decide --candidate v2
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py decide --candidate v2.1
```

```text
Release decision for v2 against v1: BLOCK
  - answer slice 'normal' drops from 7 to 6 of 8
Thresholds are illustrative (POLICY in lab.py). Latency and cost are simulated.
Release decision for v2.1 against v1: SHIP
Thresholds are illustrative (POLICY in lab.py). Latency and cost are simulated.
```

```bash
python3 weeks/week-06-rag-regression-comparisons/handson/lab.py ablate --version v2.1
```

```text
Ablation of v2.1: one component off at a time
variant               nDCG@3     R@3  answers critical  p50 ms
as configured          0.791   0.823    22/24        0     501
without rewrite        0.794   0.830    22/24        0     486
without rerank         0.811   0.860    19/24        0     432
without filtered       0.702   0.790    21/24        0     468
Latency is simulated.
```

Run the tests:

```bash
python3 -m pytest weeks/week-06-rag-regression-comparisons
```

All 10 tests pass. They check that both versions run on the same cases, the scorecard, the hidden normal-slice regression, both decisions, the gold-context swap, the ablation's disagreement between retrieval metrics and answers, and the percentile helper. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Exercises

1. **Check v2.1 against the rules by hand.** Run `scorecard` and `slices` for v2.1, then confirm each rule in `POLICY` from the numbers before running `decide`.
2. **Try a threshold of 2.5.** In the notebook, add a version identical to v2.1 with `min_score=2.5` and run the decision. Does it ship? Is it the version you would ship?
3. **Write the recommendation.** Using the five-part structure in the theory file's [worked example](../theory/week-06-rag-regression-comparisons-theory.md#102-worked-example-writing-the-recommendation), write a recommendation for the version you chose in exercise 2.
4. **Measure drift.** In the notebook, add a new current, public chunk to `CHUNKS`: a 2026-04 refund rule with a 14-day window for electronics. Rerun `retrieval_rows("v2.1")` and list the queries whose nDCG@3 changed.
5. **Explain the cost drop.** v2's simulated cost per 1,000 answers is lower than v1's. Find the cause in the scorecard and say why it is not a saving.

### Reading a failed check

Find which rule blocked the candidate before reading anything else. A slice rule names the slice. Run `paired` to see which cases moved, then `attribute` to see whether retrieval or generation caused each one, then `ablate` to see which component it belongs to.

## 2. Two debugging drills

### Drill 1: the candidate was run on fewer cases

**Break it.** Score v2 on only the first 20 answer cases and compare it with v1 on all 24. The notebook's drill cell does this.

**Symptom.** `paired` raises `KeyError: 'a-021'`. A comparison that skipped pairing would have reported 16 of 20 against 11 of 24, an 80% against 46% pass rate that looks like a triumph.

**Diagnosis.**

1. Compare the case IDs in the two result lists. They differ.
2. The candidate's set omits the four hardest restricted cases. Its rate is not comparable.
3. Pairing by ID turns a silent mismatch into an error.

**Fix and verify.** Run both versions on the same pinned case set, and assert the IDs match before comparing, as `test_both_versions_run_on_the_same_cases` does. Rerun: 18 of 24 against 11 of 24.

### Drill 2: the swap blames retrieval for an abstain case

**Symptom.** `attribute --version v2.1` reports a-021 as a retrieval failure. a-021 should abstain, and its gold evidence is empty.

**Diagnosis.**

1. Read what the swap ran: the writer with no evidence at all.
2. Any writer that abstains on empty evidence passes. The swap could not have reported generation for this case.
3. The finding is partial. Retrieval did return a lost-parcel rule that looked relevant, but the writer chose to answer from it, so generation contributed too.

**Fix and verify.** Mark the swap as inconclusive when a case has no gold sections, and investigate those cases by reading the evidence instead. The notebook's drill cell defines `attribute_with_limits`, which reports a-021 as `inconclusive`.

## 3. Completion criteria

- [ ] `lab.py decide` blocks v2 and ships v2.1, and you can state the rule that blocks v2.
- [ ] You can name the two answer cases and four queries that regressed.
- [ ] You can explain why all of v2's failures are generation failures.
- [ ] You can explain the reranker result in the ablation.
- [ ] Your recommendation states the decision, the evidence, the regressions, the latency trade-off and the follow-ups.
- [ ] `python3 -m pytest weeks/week-06-rag-regression-comparisons` reports 10 passed.

## 4. Solutions

**Exercise 1.** v2.1 has 0 critical failures. No answer slice loses a case (normal 7 to 8, outdated 0 to 4, contradictory 3 to 3, missing 0 to 4, restricted 1 to 3), and no retrieval slice loses Recall@3. Its simulated p95 is 660 ms against a budget of 615 × 1.2 = 738 ms. Every rule passes, and `decide` reports SHIP.

**Exercise 2.** A threshold of 2.5 ships too: 21 of 24, no slice loses a case against v1, and the same p95 of 660 ms. It is still worse than v2.1. It passes one case fewer, because it abstains on a-009 ("How long do I have to ask for a refund?"). The rules compare a candidate with the baseline, not with the best alternative. Choosing between two passing candidates is a separate comparison: run 2.0 against 2.5 directly, and ship 2.0.

**Exercise 3.** A good recommendation names the version and its threshold, quotes the scorecard numbers, lists the regressions found and how each was handled, states the latency change with the budget, and names follow-ups (rewriting, the four regressed queries, real latency measurement). The theory file's worked example is a model.

**Exercise 4.** Adding the 14-day electronics rule changes nDCG@3 on four queries: q-016 (0 to 0.46), q-035 (1.0 to 0.63), q-047 (0.47 to 0.43) and q-049 (0.9 to 0.75). The new chunk is unlabeled and counts as irrelevant. It takes top-3 slots from labeled sections on refund-window questions such as q-035, "Is the refund window 60 days?". A real corpus change needs relabeling. The old labels no longer describe the corpus, and the drift appears as a metric change even where the system now behaves better.

**Exercise 5.** v2 abstains on 8 cases against v1's 0, and an abstention is a short reply with few output tokens. The lower cost comes from answering less, including three answerable questions. Compare cost per correct answer instead: v1 pays 0.107 for 11 correct answers in 24, v2.1 pays the same 0.107 for 22.

**Design review.** The model answers are in the [theory file's design review](../theory/week-06-rag-regression-comparisons-theory.md#11-design-review).
