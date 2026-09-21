# Level 7: Online evaluation and the loop

*Advanced band.* Scaffold for working through
[Level 7 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-7-online-evaluation-and-the-loop).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Reference-free production metrics
- The five standard alerts
- Incident drills, canaries, and the label queue
- Online-eligibility test for scorers
- Live tracing in Phoenix

**Goal.** Measure without an answer key, alert only on what you can resolve, and carry every
finding back into a gated test.

**Notebooks & resources:** [Level 7 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-7--online-evaluation-and-the-loop)

**You are done when you can**

- give the mechanical test for whether a scorer can run online (does it read `expectations`?);
- name the first alert you would set on a production agent, and why it is not a quality metric;
- state *online discovers, offline prevents recurrence* and give the concrete step that makes it true.

---

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
