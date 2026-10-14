# Level 3: Ground truth

*Intermediate band.* Scaffold for working through
[Level 3 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-3-ground-truth).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Golden-set case anatomy (six expectations per case)
- Stratification and the refusal quota
- Dataset datasheets
- Mining production traces into eval datasets
- Provenance and merge-by-input-hash
- Synthesized vs. hand-authored cases

**Goal.** Know where cases and labels come from on day one and by month three, and the two ways
a dataset lies to you.

**Notebooks & resources:** [Level 3 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-3--ground-truth)

**You are done when you can**

- explain *circular ground truth* — why using the agent's own outputs as expectations makes it pass by construction;
- say why hand-written sets are structurally blind, and what a mined set adds that a hand-written one cannot;
- state why a curated set must not drift while a mined set must stay fresh, and why you need both.

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
