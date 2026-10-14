# Guide audits

This repository, measured against an evaluation guide written by other people. Two documents,
two jobs.

| File | What it is |
|---|---|
| [`openai-eval-guide-coverage-gaps.md`](openai-eval-guide-coverage-gaps.md) | **Audit** — OpenAI's *Evaluation best practices*, every topic badged ✅ / 🟡 / ⏭️ / ❌ against the notebook that teaches it, verified **per course**. Currently 47 / 2 / 5 / 1 across 55 rows |
| [`openai-eval-guide-tutorial.md`](openai-eval-guide-tutorial.md) | **Lesson** — the same guide in plain language, 3–4 lines per concept, one running example, and 21 TODOs that each ask you to produce something. The file is its own progress tracker. Also rendered as `openai-eval-guide-tutorial.html` on the site |

**The markdown tutorial is canonical.** The site renders it as `openai-eval-guide-tutorial.html`.
The earlier hand-built HTML version (inline SVG diagrams, tick-box tracker) is in `archive/`;
track your own progress through the 21 TODOs wherever you keep notes.

**The audit records; the tutorial teaches.** A fourth document explaining the same concepts
was folded into the tutorial and archived on 2026-09-20 — it cited no notebook the tutorial
did not already cite, which made it a second rendering rather than a second audience. See
[`../../archive/README.md`](../../archive/README.md).

## Keeping them honest

The audit carries counts, and counts are the field most likely to be wrong, because nobody
re-derives them. **Recount from the badges rather than adjusting the total** whenever a row
moves — that habit caught two errors on 2026-09-20 alone, including a row left at 🟡 after
the section closing it had already been written.

All notebook paths in these files are **relative to the repository root**, not to this
folder, so they paste straight into `jupyter lab`.
