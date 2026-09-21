# Level 8: Safety, adversarial, and multi-agent attribution

*Expert band.* Scaffold for working through
[Level 8 of the evaluation roadmap](../../docs/study-guide/evaluation-roadmap.md#level-8-safety-adversarial-and-multi-agent-attribution).
The roadmap is canonical — everything below is copied from it, so read it there if the two
ever disagree.

---

**Topics**

- Safety assertions that never get averaged
- Routing confusion matrices and handoff integrity
- Circular-handoff detection and blame attribution
- Adversarial design by attack surface
- Consent and approval gating between turns

**Goal.** Separate what must never happen from what should usually happen, test by attack
surface rather than by example, and say which agent broke a multi-agent run.

**Notebooks & resources:** [Level 8 mapping →](../../docs/study-guide/evaluation-topic-notebook-mapping.md#level-8--safety-adversarial-and-multi-agent-attribution)

**You are done when you can**

- say why a flat list of jailbreak strings tells you nothing when it passes, and what replaces it;
- design the check for "acted without asking" — a failure with no single-turn representation;
- attribute a wrong final answer in a supervisor → specialist run to the routing, the handoff, or the specialist, from the trace alone.

---

## Your work for this level

Put notebooks, scratch scripts and notes in this folder. Nothing here is wired into the
courses or the site — it is yours.

- [ ] Read or ran everything under *Notebooks & resources*
- [ ] Can answer all three *you are done when you can* checks out loud
- [ ] Wrote down the one thing that surprised me
