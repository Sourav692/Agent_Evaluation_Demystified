---
name: eval-concept-explainer
description: >-
  Explain an evaluation concept, metric, failure mode or confusing sentence in plain
  English — one concrete run with real numbers, jargon defined where it is used, a
  contrast table, one everyday analogy, and a one-line payoff. Bullets and one-liners
  over prose. Use when the user asks "explain this", "in plain english", "what does
  this mean", "why is this a weak answer", "I don't understand X", or asks for the
  same treatment applied to another case or section. Also use when adding an
  "In plain English" block to QUESTION_BANK.md, a `plain:` field to the drill page,
  or a plain-language cell to a notebook.
---

> **Paths:** `<skills-root>` means the folder that holds this skill — the parent of its base directory (e.g. `~/.claude/skills`, or a repo's `.claude/skills`). Sibling skills referenced below live there too.

# Explain it in plain English

Turns a compressed, jargon-dense passage into something a reader gets on first pass —
without dropping any of the substance.

## The rule that decides everything else

**Concrete first, abstract never on its own.** Open with one real run — real numbers,
real field names, a real trace. The general principle is what the reader *derives*
from it, not what you open with.

- "p95 went 0.9s → 5.1s while the chat model never moved" ✅
- "retrieval latency degraded significantly" ❌

## Format budget

This is the part that gets violated first. Hold to it.

| Element | Budget |
|---|---|
| Paragraphs | 2–3 sentences (see below) |
| Bullets vs prose | Bullets win any time there are ≥3 parallel items |
| Every bullet | Opens with a **bolded claim**, then the explanation |
| Contrasts | A table, not two paragraphs |
| Analogies | **Exactly one**, and only after the mechanism |
| Closing | One line. The thing worth memorising. |

**The 3-sentence cap is the rule that slips.** It is the first one to go when the
material gets interesting, and a 4-sentence paragraph is the exact point where an
explanation reverts to essay mode — the reader stops scanning and starts wading. If a
paragraph wants a fourth sentence, that is the signal it should have been a bullet list
or a table. Count them on the way out.

**No preamble.** Don't write "let's break this down" or "there are several aspects
to consider." Start at the concrete run.

## The six moves, in order

1. **One concrete run.** A trace, a snippet, a code block. Real values.
2. **Define jargon where it appears** — inline, mid-sentence, in bold.
   `**"Span" just means one recorded step.**` Never a glossary up front.
3. **Show the contrast.** The two code paths, the two traces, the two answers.
   Almost always a table with a "what it means" and a "what you fix" column.
4. **Say what each part is actually looking at.** One bullet per component,
   naming the input it reads. This is where the misunderstanding usually lives.
5. **One everyday analogy.** Inspectors, deliveries, clerks — nothing technical.
   It comes *after* the mechanism, and it never replaces it.
6. **Why it matters.** Usually: why the obvious reading is wrong, or why the
   failure is the dangerous kind.

Drop a move if the concept doesn't need it. Never reorder them.

## Hard-won specifics

- **Numbers beat adjectives.** `0.98 → 0.95 → 0.92 → 0.91` lands; "gradual erosion" doesn't.
- **Name the thing the reader can't see.** Most confusion is a missing object — a tool
  span nobody reads, an eval set that isn't production traffic. Point at it explicitly.
- **Two code paths beat a description of two code paths.**
  ```python
  raise AccountNotFound("ACC-99231")   # loud — the loop stops
  {"found": false, "balance": null}    # polite — HTTP 200, no exception
  ```
- **Check the sentence parses on first read.** "A tool that returns a soft failure
  object instead of raising hands the model something" is a garden path — two technical
  words collide. Add the comma, or rewrite.
- **When correcting a wrong intuition, concede the correct part first.** "Your instinct
  isn't wrong — it's one of four candidates" earns the rest of the explanation.
- **Don't hedge.** "It may sometimes be the case that" → delete.

## Where the block goes

| Target | How |
|---|---|
| `docs/interview-prep/QUESTION_BANK.md` | `**In plain English:**` block, after the talk-through, before **The trap** |
| `docs/interview-prep/evaluation-round-drill.html` | Add a `plain:"…"` field (HTML string) to the case object in `CASES`. `quizCard()` renders the collapsible automatically. **Escape newlines as `\n`** — a literal newline in a JS string breaks the whole page silently |
| `docs/concepts/*.md` | Inline, at the section it explains |
| `courses/**/*.ipynb` | A markdown cell following `<skills-root>/format-notebook/SKILL.md` |

**Both surfaces or neither.** If the passage exists in both the bank and the drill,
update both in the same change — they drift otherwise.

**The budget covers anything you write alongside.** If the task also wants placement
notes, a summary, or a hand-off memo, those get the same treatment — same paragraph cap,
same bullets-over-prose. A tight explanation delivered under a wall of prose notes
undoes the point.

## Verify before claiming done

- [ ] Opens on a concrete run, not a definition
- [ ] Every paragraph ≤3 sentences
- [ ] Exactly one analogy, placed after the mechanism
- [ ] Every jargon term defined at first use
- [ ] Closing line is one sentence
- [ ] If HTML: page still parses — extract the inline `<script>` and run
      `osascript -l JavaScript -e '… new Function(src) …'`, then open it and look
- [ ] If both bank and drill carry the passage: both updated

## Worked example

`docs/interview-prep/QUESTION_BANK.md`, Cases 5 and 6, are the reference
implementations of this format. Read Case 5 before writing a new one.

**In miniature** — the shape, on "polite tool failure":

> One concrete run. A user asks *what's the balance on account ACC-99231?*
>
> ```
> 1. USER INPUT   "What's the balance on ACC-99231?"
> 2. TOOL SPAN    got back { found: false, balance: null }
> 3. FINAL OUTPUT "Your Premium plan has a balance of $45.20."
> ```
>
> That account doesn't exist. Nothing crashed.
>
> **"Span" just means one recorded step.**
>
> **What each scorer is actually looking at:**
> - **Groundedness** compares the answer to *retrieved documents*. There are none here.
> - **Task success** reads the *final string*. It reads beautifully. Pass.
>
> **Step 2 — the only place the failure is visible — is read by nobody.**
>
> **The analogy.** Two inspectors sign off a clerk's report. Neither asks the clerk
> what they actually found when they went to look.
>
> **Why it's dangerous.** The checks aren't weak. The failure happens somewhere no
> check is pointed — the dashboard is green, and honestly green.

## Anti-example

What this skill exists to prevent:

> Tool failure evaluation is an important consideration in agentic systems. There are
> several dimensions to consider when a tool does not behave as expected. It is
> generally advisable to ensure that appropriate monitoring is in place, as failures
> may not always surface through standard evaluation mechanisms.

No run, no numbers, no named component, nothing to act on, and three hedges.
