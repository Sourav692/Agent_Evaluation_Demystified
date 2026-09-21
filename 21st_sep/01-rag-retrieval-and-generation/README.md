# Level 1: RAG (retrieval and generation)

*Beginner band.* Scaffold for working through
[Level 1 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-1-rag-retrieval-and-generation).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Deterministic retrieval metrics (Precision@K, Recall@K, MRR, nDCG)
- LLM-judged retrieval metrics (contextual precision, recall, relevancy)
- Referenceless generation metrics (faithfulness, answer relevancy, hallucination)
- Reference-based generation metrics (answer correctness, semantic similarity)
- Evaluation as LangGraph pipeline gates
- RAGAS as a second opinion, and the pytest/CI pattern
- Building a RAG system and synthesizing a golden set
- Writing rubrics that avoid a vague judge

**Goal.** Separate a retrieval failure from a generation failure with numbers, and know the
one failure no referenceless metric can see.

**Notebooks & resources:** [Level 1 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-1--rag-retrieval-and-generation)

**You are done when you can**

- diagnose "low precision" vs "low recall" into two different fixes (reranking / smaller top-k vs chunking / larger top-k / query rewriting);
- explain why groundedness stays satisfied when retrieval was insufficient — and which metric would have caught it;
- say what a "faithful, relevant, and completely wrong" answer is, and why only a reference-based check sees it.

---

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
