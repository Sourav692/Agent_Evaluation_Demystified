---
name: "explainer"
description: "Build or audit a level's Explainer.md in this Agent-Evaluation-Demystified repo — a standalone, beginner-friendly conceptual write-up merging every source doc for that roadmap level with no duplication."
---

# Explainer

Generates (or audits) `Explainer.md` for one level of the evaluation roadmap in the
`Agent_Evaluation_Demystified` repo — the file that lives in `21st_sep/<NN-level-slug>/`
alongside that level's scaffold `README.md`. One Explainer.md per level. Works for any level
(0 through 9, or the Databricks-track phases) — the level number/name is the only input that
changes.

This skill encodes the project's own custom instructions (below) plus the exact review
discipline that closed real coverage gaps the first time this was run for Level 0 — so run
the full checklist even when the task feels done after the first draft.

## When to use this

- The user asks to "create the conceptual/explainer for Level N", "build Explainer.md for
  [level name]", or points at a `21st_sep/NN-.../` folder and asks for its write-up.
- The user asks to review/audit an existing `Explainer.md` for missed content from its
  sources.
- The user asks to extend or refresh an Explainer.md after the roadmap or a source doc changed.

## Step 0 — Respect the project's own instructions first

This repo's Project instructions govern *any* conceptual/theoretical tutorial material,
Explainer.md included:

1. **Check coverage before writing anything.** Search the repo for whether the concept is
   already covered (it almost always is — that's the whole point of Explainer.md: it never
   introduces a new concept, it only consolidates existing ones).
2. **If already covered, don't silently just write the file** — normally for *new* material
   you'd stop and ask the user what to do next. For Explainer.md specifically, the answer is
   always "consolidate the existing coverage into one file" — that's the deliverable — so this
   step is satisfied by doing Step 2 below thoroughly, not by asking again each time.
3. **Beginner-friendly, plain language.** No unexplained jargon; define every technical term
   in plain words the first time it appears.
4. **Use examples and analogies** wherever they improve understanding (the support-agent /
   refund running example, the ROUGE-L false-positive table, etc. — reuse the source's own
   worked examples rather than inventing new ones).
5. **Organize logically** — this skill's Step 3 gives the section order that has worked.
6. **End with a references section** listing every source used (Step 5 gives the required
   format).
7. **Never invent references or claim to have reviewed material that wasn't actually read.**
   State limitations plainly (see the Limitations paragraph template in Step 5).

## Step 1 — Identify the level and gather every source for it

1. Find the target level's row in `docs/study-guide/evaluation-roadmap.md` — this gives the
   level's **topic list** and **goal statement**. Every topic named there must end up covered
   somewhere in Explainer.md.
2. Find the same level's row in `docs/study-guide/evaluation-topic-notebook-mapping.md` — this
   gives the **exact source documents** for that level (notebook(s), field-guide section(s),
   interactive lab page(s), question-bank section(s)) plus each one's **cost tag**
   (none/key/cached/workspace).
3. Confirm the destination: `21st_sep/<NN-level-slug>/Explainer.md`, next to that folder's
   existing scaffold `README.md`. Read the README first — it already contains the roadmap's
   topic list, goal, and "you are done when you can" checklist for that level. **Never
   duplicate the README's checklist inside Explainer.md** — leave it where it is.
4. Read **every** source file in full — not skimmed, not the first N characters. For a
   notebook, parse cell-by-cell (`json.load` + iterate `cells`, print full `source` per cell,
   not truncated). For a long markdown field guide, extract the exact section range for that
   level (e.g. `sed -n '<start>,<end>p'`) and read it whole. For an HTML interactive lab,
   strip tags and read the full text, not just the first several KB. Missing this step is
   exactly how the first draft of Level 0's Explainer.md ended up with real gaps (see Step 6).
5. Files on the user's connected device are read/written via `device_bash` (mounted under
   `$HOME/mnt/<folder>/...`), never staged into the cloud container just to read them — this
   repo lives on the user's machine, not in the sandbox.

## Step 2 — Resolve real ambiguities with the user before drafting ("grill me")

Do not silently guess on forks that change the shape of the document. Use `AskUserQuestion`
(recommended option first) for things like:

- **Name collisions across sources.** More than one source may use the same name for two
  different ideas (e.g. this repo has two unrelated things both called a "cost ladder" — a
  scorer-sophistication ladder in the field guide and a dollar-cost tag ladder in the
  notebook-mapping doc). Ask which the user wants, or whether to cover both, clearly labeled.
- **Diagram format.** Mermaid (matches this repo's existing `QUESTION_BANK.md` precedent, and
  renders on GitHub) vs. plain tables/ASCII. Default recommendation: Mermaid.
- **Question-bank scope.** `QUESTION_BANK.md` is organized by *interview-round part*, not by
  roadmap level. For each level, work out exactly which part/section is genuinely specific to
  that level's material (cross-check against the roadmap's own "Rehearsal" pointers for that
  level) and confirm the exact boundary with the user rather than assuming "the whole file" or
  "just one line item."
- **Runnable code snippets.** If a source notebook includes a small illustrative code snippet
  backing a worked example (e.g. the ROUGE-L/BLEU function), ask whether Explainer.md should
  show that code or just the resulting table/output, since Explainer.md is meant to be a
  conceptual (non-executable) companion, not a copy of the notebook.

Skip this step only if the user has already answered these exact questions for a prior level
in the same session and said the same answers should carry forward.

## Step 3 — Draft Explainer.md

Structure that has worked well (adapt section count to the level's actual topic list — don't
pad or omit):

1. **Title + "who this is for" callout.** State that no prior tool knowledge is assumed and
   every term is defined on first use.
2. **"Why this level exists"** — one short framing paragraph connecting the level's topics to
   a concrete running example (reuse the source material's own example system where one
   exists, e.g. the refund-issuing support agent).
3. **One numbered section per major topic from the roadmap's topic list**, each one merging
   *every* source's treatment of that topic into a single explanation — never split the same
   topic across two sections, and never repeat a diagram/table/example that's already been
   shown once (link back to the earlier section by name instead, e.g. "the same taxonomy
   covered in Section 1, not repeated here").
4. **Diagrams**: a Mermaid `flowchart` for any decision procedure (a yes/no branching
   question), any layered taxonomy, or any multi-step loop/spine. A table is fine for anything
   that's fundamentally tabular (comparisons, cost tags, tool lists) — don't force a diagram
   where a table already reads clearly.
5. **A "question-bank corner"** as its own titled section near the end, scoped per Step 2's
   agreed boundary, explicitly noting anything it deliberately does NOT repeat (e.g. a
   taxonomy diagram already drawn earlier in the file).
6. **References**, per Step 5 below.

Writing style: plain language, definitions on first use, tables/bullets over dense prose
(matches this user's stated preference for headers and bullet structure), reuse the sources'
own worked examples and numbers rather than inventing new ones, and preserve exact figures
(e.g. "0.94", "2,500+ calls", "~606 scored traces") verbatim from source — these are load-
bearing details, not filler.

## Step 4 — Write the file

The repo lives on the user's connected device, not in the cloud sandbox. Write (or edit)
`Explainer.md` directly with `device_bash` — a heredoc (`cat > path << 'EOF' ... EOF`, quoted
to stop shell expansion of `$`/backticks) for a fresh file, or a small Python script doing
targeted `str.replace()` calls against exact anchor strings for edits to an existing file
(safer than `sed` for multi-line markdown). Always re-read the written file back afterward to
confirm the edit landed exactly once (`assert anchor in content` before replacing).

## Step 5 — References section format

Always end with a `## References` section, split into two labeled groups exactly like this
(the user asked for this split explicitly and it should be the default for every level, not
just re-requested each time):

```markdown
## References

All content above was drawn only from material already in this repository. Nothing here was
invented, and no external source was consulted.

**Notebook:**

- `path/to/notebook.ipynb` — what it contributed to this file, specifically.

**Docs:**

- `path/to/field-guide.md`, §X.Y–X.Z — what it contributed.
- `path/to/interactive-lab.html` — what it contributed (note explicitly if it introduced
  nothing beyond what a doc source already covered, rather than re-listing the same content
  as if it were new).
- `path/to/QUESTION_BANK.md`, Part N (§N.1–N.3) — what it contributed, and note explicitly
  which parts of that file were judged out of scope for this level.
- `docs/study-guide/evaluation-roadmap.md` — used to scope the topic list, not quoted
  directly.
- `docs/study-guide/evaluation-topic-notebook-mapping.md` — used for the resource list and
  cost tags.

**Limitations.** This file was written by reading the repository's own material, not by
running any notebook or calling any API — no cost was incurred producing it, consistent with
this project's rule against executing anything that spends money without being asked. It does
not independently verify [any third-party tool/vendor named in the level]'s own documentation;
descriptions of that tool are this repository's characterization, not a review of the vendor's
docs.
```

If a level has more than one notebook, list every one under **Notebook:** as its own bullet
(don't collapse them). If a level's docs span more than the five categories above, keep the
two-group split (**Notebook:** / **Docs:**) and just add more bullets under **Docs:**.

## Step 6 — Mandatory completeness review (do this even when the draft feels done)

This is the step that actually caught real gaps the first time — treat it as required, not
optional, for every level:

1. Re-open every source file **in full** a second time, independently of memory of what you
   just wrote (don't trust your own draft's References list as a proxy for "I covered this").
2. For each source, walk it section-by-section / cell-by-cell and check off each distinct
   claim, table, bullet list, or named concept against Explainer.md. Common miss patterns
   seen already on this repo:
   - A named concept/behavior that's listed in one source's table but doesn't fit the
     organizing scheme Explainer.md chose for its main sections (e.g. a taxonomy dimension
     that's orthogonal to the others). Don't drop it — add a short callout that explains why
     it doesn't fit the main structure and points to where it's covered in depth elsewhere in
     the roadmap.
   - A single row dropped from an otherwise-transcribed table (e.g. a "runs in CI?" row).
   - A named bullet in a failure-modes / gotchas list that reads similar to a neighboring
     bullet but is actually distinct (e.g. "nobody validates the validator" vs. "measure
     agreement, not average" — both about judges, both different claims).
   - A "when X is actually fine to use" counter-section that follows a "here's where X fails"
     example — tutorials often pair these, and it's easy to keep only the failure half.
   - A cross-cutting nuance that a table or diagram alone can't show — e.g. "this split cuts
     across the taxonomy, not along it," backed by one named exemplar pair.
3. List every gap found explicitly to the user before or while fixing (don't silently patch
   and only summarize the final state) — the user should be able to see exactly what was
   missing and exactly what was added for it.
4. Apply fixes as surgical, anchored edits (Step 4's Python `str.replace` approach) rather than
   rewriting the whole file, so nothing else drifts.
5. Also explicitly name anything deliberately still excluded and why (e.g. course
   navigation/table-of-contents content that isn't a concept; a checklist that already lives in
   the level's README and shouldn't be duplicated). A reviewer should never have to wonder
   whether an omission was noticed and judged out-of-scope, versus simply missed.

## Reusing this for a different level

Everything above is level-agnostic except: the specific topic list (from the roadmap), the
specific source files (from the notebook-mapping doc), the specific running example (reuse
whatever example system that level's own sources already use), and the specific
question-bank section boundary (Step 2). Don't assume a new level's sources have the same
shape as Level 0's (e.g. not every level will have exactly one notebook, or exactly one
interactive lab) — Step 1 is what discovers the actual source set each time.