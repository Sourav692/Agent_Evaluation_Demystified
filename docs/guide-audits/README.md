# Guide audits

This repository, measured against evaluation guides written by other people. Three documents,
two jobs. (Four files: the tutorial also ships as a page — see below.)

| File | What it is |
|---|---|
| [`openai-eval-guide-coverage-gaps.md`](openai-eval-guide-coverage-gaps.md) | **Audit** — OpenAI's *Evaluation best practices*, every topic badged ✅ / 🟡 / ⏭️ / ❌ against the notebook that teaches it, verified **per course**. Currently 47 / 2 / 5 / 1 across 55 rows |
| [`openai-eval-guide-tutorial.md`](openai-eval-guide-tutorial.md) | **Lesson** — the same guide in plain language, 3–4 lines per concept, one running example, and 21 TODOs that each ask you to produce something. The file is its own progress tracker. Also rendered as [`openai-eval-guide-tutorial.html`](openai-eval-guide-tutorial.html) |
| [`genai-eval-playbook-coverage-map.md`](genai-eval-playbook-coverage-map.md) | **Audit** — *LLM Evaluation for GenAI Forward Deployed Engineers*, a customer-facing playbook. All 20 sections mapped; thirteen open gaps, clustered in commercial apparatus and retrieval operations |

**The markdown tutorial is canonical.** `openai-eval-guide-tutorial.html` is the same
seven chapters as a browser page — the Mermaid blocks drawn as inline SVG, the 21 TODOs as
tick boxes with a progress meter saved in the browser. Edit the `.md` and re-render; the page
is not a second source. It carries no content the markdown does not.

**The audits record; the tutorial teaches.** A fourth document explaining the same concepts
was folded into the tutorial and archived on 2026-09-20 — it cited no notebook the tutorial
did not already cite, which made it a second rendering rather than a second audience. See
[`../../archive/README.md`](../../archive/README.md).

## Why two audits and not one

They ask different questions of the same repo, and the answers barely overlap.

| | OpenAI's guide | The FDE playbook |
|---|---|---|
| Asks | "How do you evaluate this?" | "How do you prove it to a customer and get sign-off?" |
| This repo scores | Near-total — 1 open gap | Thin — 13 open gaps |
| Where the gaps fall | A vendor API surface | Acceptance criteria, sign-off owners, dashboards, staged rollout, retrieval operations |

The two overlapped in exactly one item — ROUGE / BLEU / BERTScore — **closed in both** on
2026-09-20 by `courses/01-rag-agent-tool-evaluation/00_Evaluation_Landscape.ipynb` §1c.
Everything else is disjoint, which is the useful finding: closing one list does not shorten
the other.

## Keeping them honest

Both audits carry counts, and counts are the field most likely to be wrong, because nobody
re-derives them. **Recount from the badges rather than adjusting the total** whenever a row
moves — that habit caught two errors on 2026-09-20 alone, including a row left at 🟡 after
the section closing it had already been written.

All notebook paths in these files are **relative to the repository root**, not to this
folder, so they paste straight into `jupyter lab`.
