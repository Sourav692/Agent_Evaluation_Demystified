# Level 0: Orientation

*Beginner band.* Scaffold for working through
[Level 0 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-0-orientation).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Evaluation taxonomy: reference-based vs. referenceless
- LLM-judge failure modes and the code-vs-judge decision
- The four-framework map (RAGAS, DeepEval, MLflow, Phoenix)
- Reference-free metrics and their blind spots (ROUGE-L)
- The five-layer diagram: retrieval, generation, tool mechanics, trajectory, outcome
- What breaks where: symptom → metric → cost
- Offline vs. online: the two deciding questions
- The cost ladder: none → key → cached → workspace

**Goal.** Draw the taxonomy from memory and choose between a deterministic scorer and a judge
without hesitating. Every follow-up later is a disguised version of *"which layer are you
measuring?"*

**Notebooks & resources:** [Level 0 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-0--orientation)

**You are done when you can**

- name the five surfaces and, for each, one metric that needs an answer key and one that does not;
- say why *"if code can check it, checking it with a judge is waste"* is a cost argument *and* a reproducibility argument;
- explain in one sentence why reference-based metrics cannot run on production traffic.

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
