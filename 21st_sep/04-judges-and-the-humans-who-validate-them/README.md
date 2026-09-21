# Level 4: Judges, and the humans who validate them

*Intermediate band.* Scaffold for working through
[Level 4 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-4-judges-and-the-humans-who-validate-them).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Building judges three ways (GEval, DAGMetric, rubrics)
- Judge bias: position bias, same-model bias, verbosity
- Human feedback and calibration (Cohen's kappa)
- The rubber-stamp signal
- Custom scorers and trace-based judges
- Judge alignment to expert labels

**Goal.** Build a judge three ways, catch it lying three ways, and know the only thing that
licenses trusting it.

**Notebooks & resources:** [Level 4 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-4--judges-and-the-humans-who-validate-them)

**You are done when you can**

- explain why *exact agreement flatters* on skewed distributions and when quadratic weighted kappa is the right default (two judges: identical 0.00 exact agreement, +0.71 vs −0.82 weighted);
- answer "your judge and your domain expert disagree on 20 % of cases" with a procedure, not a shrug;
- say what *rubber-stamping* looks like in the data and why it is a signal about the reviewer, not the agent.

---

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
