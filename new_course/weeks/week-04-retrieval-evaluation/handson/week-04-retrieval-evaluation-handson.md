# Week 4 hands-on: Retrieval evaluation

Read the [theory](../theory/week-04-retrieval-evaluation-theory.md) first. This file holds the lab, the debugging drills, the completion checklist and the solutions.

## 1. Lab

### Files

```text
new_course/
  datasets/
    policies/refund-policy-2026-01.md     # current refund policy (public)
    corpus/                               # 6 more help-centre documents, one superseded, one internal
    retrieval/policy-queries-v1.jsonl     # 50 queries with graded section labels
  shared/
    retrieval.py                          # corpus loader, chunkers, bm25, concept, hybrid
  weeks/week-04-retrieval-evaluation/
    README.md                             # week index
    theory/week-04-retrieval-evaluation-theory.md   (and .html)
    handson/
      week-04-retrieval-evaluation-handson.md   # this file
      week-04-retrieval-evaluation-handson.ipynb   # the same lab as a notebook
      lab.py                              # metrics, benchmark, comparisons
      tests/test_lab.py
    dataset/
      README.md                           # what each file is
      hand_rankings.jsonl                 # three fixed rankings to check by hand
```

The query set and the corpus live at the course root because Week 6 reuses them.

### The notebook

`week-04-retrieval-evaluation-handson.ipynb` in this folder walks through the same lab one step per cell: it defines the functions from `lab.py` (a test keeps the code identical), runs them, prints the results and ends with the drills. Select the course `.venv` as its kernel. It needs no API key.

### Setup

Setup is the same as Week 1. The lab uses only the standard library.

### What is in a query

```json
{"query_id": "q-046", "query": "My final-sale rug arrived damaged 3 days ago, can I get a refund?", "slice": "multi_section", "relevance": {"refund-policy-2026-01#R3": 3, "shipping-policy-2026-01#S3": 2, "refund-policy-2026-01#R2": 1}, "label_source": "author-labeled, one annotator"}
```

`relevance` maps a policy section to its grade. A chunk's grade is the highest grade among the sections it covers.

### The metrics

The five metric functions take the ranked chunks, the labels and k:

```python
def precision_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """Share of the top k chunks that are relevant at all (grade > 0)."""
    return sum(chunk_grade(c, labels) > 0 for c in ranked[:k]) / k


def recall_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """Share of the labeled sections that some top-k chunk covers."""
    covered = {s for c in ranked[:k] for s in c.section_ids if s in labels}
    return len(covered) / len(labels)


def reciprocal_rank_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """1 / rank of the first relevant chunk in the top k, or 0. Averaged over queries it is MRR."""
    for rank, c in enumerate(ranked[:k], start=1):
        if chunk_grade(c, labels) > 0:
            return 1 / rank
    return 0.0


def ndcg_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    credited: set[str] = set()
    dcg = 0.0
    for rank, c in enumerate(ranked[:k], start=1):
        new = [s for s in c.section_ids if s in labels and s not in credited]
        credited.update(new)
        grade = max((labels[s] for s in new), default=0)
        dcg += (2 ** grade - 1) / math.log2(rank + 1)
    ideal = sorted(labels.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(rank + 1) for rank, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0
```

`hit_rate_at_k` returns 1.0 when any top-k chunk is relevant. `score_query` returns all five plus `violations` (superseded or internal chunks in the top k) and `words` (the context size).

### Run it

All commands run from `new_course/`. Output below is from Python 3.12.10.

Check the hand rankings. Work them out on paper first, using the theory file's [worked examples](../theory/week-04-retrieval-evaluation-theory.md#6-the-metrics-by-hand):

```bash
python3 weeks/week-04-retrieval-evaluation/handson/lab.py hand
```

```text
H1 outdated policy ranked first: labels {'refund-policy-2026-01#R2': 3}
  k=3  precision=0.333  recall=1.000  hit=1.000  mrr=0.500  ndcg=0.631
  k=5  precision=0.200  recall=1.000  hit=1.000  mrr=0.500  ndcg=0.631
H2 related sections first, the answer at rank 4: labels {'refund-policy-2026-01#R3': 3, 'shipping-policy-2026-01#S3': 2, 'refund-policy-2026-01#R2': 1}
  k=3  precision=0.667  recall=0.667  hit=1.000  mrr=1.000  ndcg=0.387
  k=5  precision=0.600  recall=1.000  hit=1.000  mrr=1.000  ndcg=0.708
H3 the best possible order: labels {'refund-policy-2026-01#R3': 3, 'shipping-policy-2026-01#S3': 2, 'refund-policy-2026-01#R2': 1}
  k=3  precision=1.000  recall=1.000  hit=1.000  mrr=1.000  ndcg=1.000
  k=5  precision=0.600  recall=1.000  hit=1.000  mrr=1.000  ndcg=1.000
```

Run the full comparison:

```bash
python3 weeks/week-04-retrieval-evaluation/handson/lab.py compare
```

```text
Retrievers, filtered to current public policy, section chunks:
retriever @ k                     P@k     R@k     Hit     MRR    nDCG   viol   words
bm25 @ 3                        0.313   0.740   0.840   0.767   0.709      0      87
bm25 @ 5                        0.212   0.800   0.880   0.775   0.731      0     147
concept @ 3                     0.353   0.810   0.880   0.830   0.767      0      84
concept @ 5                     0.240   0.897   0.940   0.843   0.808      0     141
hybrid @ 3                      0.347   0.813   0.880   0.817   0.764      0      86
hybrid @ 5                      0.240   0.903   0.960   0.835   0.808      0     142

Metadata filter, hybrid @ 5:
filter                            P@k     R@k     Hit     MRR    nDCG   viol   words
off                             0.220   0.850   0.900   0.724   0.731     57     139
on                              0.240   0.903   0.960   0.835   0.808      0     142

Chunking, hybrid @ 5, filtered:
chunking                          P@k     R@k     Hit     MRR    nDCG   viol   words
section                         0.240   0.903   0.960   0.835   0.808      0     142
window                          0.344   0.900   0.940   0.828   0.796      0     122
document                        0.244   1.000   1.000   0.907   0.891      0     529
```

Break one configuration down by slice, worst recall first:

```bash
python3 weeks/week-04-retrieval-evaluation/handson/lab.py slices --retriever bm25 --k 5
```

```text
bm25 @ 5 by slice (filtered, section chunks):
slice (queries)                   P@k     R@k     Hit     MRR    nDCG   viol   words
paraphrase (10)                 0.120   0.500   0.600   0.323   0.316      0     152
multi_section (5)               0.360   0.667   1.000   1.000   0.730      0     154
outdated_trap (6)               0.233   0.833   0.833   0.750   0.705      0     148
exact_term (8)                  0.200   0.875   0.875   0.875   0.875      0     144
restricted_trap (5)             0.200   0.900   1.000   0.900   0.891      0     140
direct (16)                     0.225   0.948   1.000   0.906   0.878      0     147
overall (50)                    0.212   0.800   0.880   0.775   0.731      0     147
```

Inspect one query's ranking, with the filter off:

```bash
python3 weeks/week-04-retrieval-evaluation/handson/lab.py query q-035 --retriever hybrid --k 5 --unfiltered
```

```text
q-035 (outdated_trap): Is the refund window 60 days?
labels: {'refund-policy-2026-01#R2': 3}
  1. refund-policy-2026-01#R2               grade 3
  2. refund-policy-2025-06#R2               grade 0  <- superseded/public
  3. payments-policy-2026-01#P2             grade 0
  4. shipping-policy-2026-01#S3             grade 0
  5. refund-escalation-playbook-2026-01#I2  grade 0  <- current/internal
  precision=0.200  recall=1.000  hit=1.000  mrr=1.000  ndcg=1.000  violations=2.000  words=149.000
```

Run the tests:

```bash
python3 -m pytest weeks/week-04-retrieval-evaluation
```

All 12 tests pass. They check the query set, the three hand rankings, the precision cap, that nDCG never exceeds 1 with window chunks, the slice results above, the filter's violation count and the chunking trade-off. The last three check that the notebook uses the same code as `lab.py`, that it runs offline from top to bottom, and that the theory HTML matches its Markdown.

### Optional: real embeddings (paid)

The concept vector is a stand-in. To compare a real embedding model with the same queries and metrics:

```bash
pip install -r requirements-integrations.txt   # with .venv active
export OPENAI_API_KEY=...                       # never commit it
python3 weeks/week-04-retrieval-evaluation/handson/lab.py dense-live --model text-embedding-3-small
```

It makes two embeddings calls: one for the 26 chunks and one for the 50 queries, a few thousand tokens in all. Check your provider's current price first. It prints `dense` and `dense + bm25 hybrid` rows in the same format as `compare`.

**Validation status:** when this guide was written, `dense-live` had been checked against the installed `openai` 2.54.0 package (`embeddings.create(input=..., model=...)`) but had not been run against a model. Until it runs, the dense-versus-hybrid comparison in this course is measured only with the concept-vector stand-in.

### Exercises

1. **Hand-check H2 at k = 5.** Before running `hand`, calculate Precision@5, Recall@5, MRR and nDCG@5 for ranking H2.
2. **Review five labels.** Without running anything, grade every current public section for queries q-008, q-021, q-030, q-043 and q-047 from the policy text. Compare with the labels in `policy-queries-v1.jsonl` and note where you disagree.
3. **Explain a miss.** q-016 ("I changed my mind about the jacket, can I send it back?") misses for all three retrievers. Use `query q-016` and the tokenizer in `shared/retrieval.py` to find out why.
4. **Choose k.** From the `compare` output, pick k for production and defend it with recall, precision and words sent.
5. **Run the restricted traps unfiltered.** Run `query` with `--unfiltered` on q-041 to q-045. Which internal sections appear, and for which queries?

### Reading a failed test

A failed metric test means either the metric code or the data changed. Rerun `hand` first: if the hand rankings still match the worked examples, the metric code is fine and the corpus, the labels or a retriever changed. Every benchmark number in this file depends on the exact corpus and query set. Any edit to them changes the expected values.

## 2. Two debugging drills

### Drill 1: the exact rule number finds nothing

**Symptom.** `query q-005 --retriever bm25` ("What does section R6 of the refund policy cover?") returns five chunks with grade 0. BM25 is supposed to be good at exact terms.

**Diagnosis.**

1. Print the chunk text for `refund-policy-2026-01#R6`: "One refund per order. An order can be refunded once…". The label "R6" is in the chunk ID, not the text.
2. Tokenize the query: `r6` is its rarest token, and no chunk contains it.
3. The retriever cannot match a word the chunker threw away.

**Fix and verify.** Put the section label into the text the retriever scores, such as `R6. One refund per order. …`. The notebook's drill cell rebuilds the chunks that way and reruns q-005: the R6 section moves to rank 1. Changing `shared/retrieval.py` itself would change every benchmark number in this file. Treat it as a candidate change and measure the whole set before adopting it.

### Drill 2: nDCG above one

**Break it.** Score nDCG by giving every chunk its own grade, with no once-per-section rule. The notebook's drill cell defines that version as `ndcg_double_credit`.

**Symptom.** With window chunks, hybrid at k = 5 averages nDCG 1.051. A normalized score above 1 is impossible.

**Diagnosis.**

1. Find the queries with nDCG above 1, and print their rankings.
2. Two or three windows in the top 5 come from the same relevant section.
3. Each window earned that section's full gain, while the ideal ranking counts each section once. The numerator counted more relevance than exists.

**Fix and verify.** Credit each labeled section once, as `ndcg_at_k` does. Rerun the chunking comparison: window nDCG drops to 0.796. The test `test_ndcg_never_exceeds_one_with_window_chunks` guards it.

## 3. Completion criteria

- [ ] Your hand calculations for H1 and H2 match `lab.py hand`.
- [ ] `lab.py compare` output matches section 1, and you can name the slice each retriever wins.
- [ ] You can explain why the filter matters even though recall changes by only 0.05.
- [ ] You found the cause of the q-016 miss.
- [ ] You chose a production k and defended it with three numbers.
- [ ] `python3 -m pytest weeks/week-04-retrieval-evaluation` reports 12 passed.

## 4. Solutions

**Exercise 1.** At k = 5, the relevant chunks are S3 (rank 1), R2 (rank 2) and R3 (rank 4). Precision@5 = 3/5 = 0.6. Recall@5 = 3/3 = 1.0. MRR = 1/1 = 1.0. DCG@5 = 3/1 + 1/1.585 + 7/2.322 = 3 + 0.631 + 3.015 = 6.646, IDCG = 9.393, nDCG@5 = 0.708.

**Exercise 2.** No single answer. Two places a second labeler might differ: q-043 ("Is there compensation for a late delivery?") has no public section that answers it, and the labels give S1 and S2 low grades for related context. Some labelers would leave it unlabeled and drop it from the retrieval set. q-047 (a $700 laptop) labels R2 at grade 2. The window is not in question for a damaged item reported promptly, and grade 1 is also defensible. Record disagreements and resolve them before comparing retrievers on those queries.

**Exercise 3.** Two tokenizer facts combine. The policy text says "change-of-mind", which the tokenizer turns into the single token `changeofmind`, so "changed my mind" never matches it in BM25. In the concept lexicon, "changed" belongs to the `address` concept (as in "address changed"), so the concept vector pulls the query toward the delivery-address section. Fixes: keep hyphenated words as separate tokens, and give the lexicon a "change of mind" concept. Measure the whole set after either change.

**Exercise 4.** k = 5 is the defensible choice here. It adds 0.06 to 0.09 recall over k = 3 for every retriever, at about 55 more words per query, and hybrid's hit rate reaches 0.96. Going further is a trade the answer writer must justify in Week 5: precision keeps falling, and so does the share of the context that is useful.

**Exercise 5.** With hybrid at k = 5 and the filter off:

| Query | Excluded chunks in the top 5 |
| --- | --- |
| q-041, refund to a new card | playbook I2 (fraud signals) at rank 2 |
| q-042, who approves $3,000 | superseded 2025-06 R4 at rank 3 and R2 at rank 5 |
| q-043, compensation for a late delivery | playbook I3 (goodwill credits) at rank 1 |
| q-044, can a specialist approve | playbook I1 (approval limits) at rank 1, superseded R4 at rank 4 |
| q-045, refund to a different bank account | playbook I2 at rank 3 |

Two internal sections rank first, above every public passage. q-042 shows that a restricted trap can also pull in the superseded policy. The filter must handle both conditions, status and audience.

**Design review.** The model answers are in the [theory file's design review](../theory/week-04-retrieval-evaluation-theory.md#11-design-review).
