# Level 6: The release gate and CI

*Advanced band.* Scaffold for working through
[Level 6 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-6-the-release-gate-and-ci).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- The four-check release gate
- Free CI gate vs. paid evaluation job
- Prompt registry and production aliasing
- The two-condition promotion gate
- Optimizer scores vs. the same gate

**Goal.** Turn metrics into a decision that can refuse a deploy, and put the cost of loosening
it on a named line.

**Notebooks & resources:** [Level 6 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-6--the-release-gate-and-ci)

**You are done when you can**

- explain why a threshold-only gate permits erosion (0.98 → 0.91 clears 0.90) and why a regression-only gate ships a bad baseline's improvement;
- say why the same −0.015 delta blocks on a deterministic metric and is tolerated on a judged one;
- describe a gate that fails a PR without spending a cent, and where the money is spent instead.

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
