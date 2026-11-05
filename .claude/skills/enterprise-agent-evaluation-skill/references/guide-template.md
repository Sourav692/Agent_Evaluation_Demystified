# Default weekly guide template

A full weekly guide is two files: a theory file in `theory/` and a hands-on file in `handson/`, laid out as described under Deliverable format in `SKILL.md`. For other modes, keep only the sections required by `SKILL.md`. Replace placeholders with descriptive topic names and adjust the time estimate to the actual work.

Write explanations as short, connected paragraphs. Under theory, group related concepts into descriptive third-level topic headings. Define each new term before using it, explain the mechanism, and connect it to the worked example. The bullets below describe coverage, not a required bullet-only output format. Avoid repeating the same explanation across theory, the worked example, and the memory card.

## Theory file: `theory/<week>-theory.md`

The theory file follows the repository's field-guide format (reference: `docs/concepts/field-guide/02-rag-retrieval.md`, rendered as `site/dist/field-guide-02-rag-retrieval.html`). `tools/build_html.py` runs it through the same `site/build.py` transforms, so the Markdown conventions below are what produce the page's features. Week 1's theory file is the worked reference.

Skeleton, in order:

```markdown
# Week XX theory: [Precise topic]

*<Tagline: one sentence naming the tension, not the topic.>*

◷ N min read · Week XX of 16 · <Difficulty> · [Course index](../../../README.md)

> **Before you start.** What this page assumes (link earlier weeks' theory files), the policy or
> data it relies on, and a link to the hands-on file.

*Lab: `handson/lab.py` · Notebook: `<week>-handson.ipynb` · Data: `dataset/...`*

---

## 1. What this week builds
**Project state.** ... **Time.** ... then 3-5 numbered outcomes and the files the week adds.

---

## 2. <The concrete failure, as a noun phrase>
### 2.1 ... ### 2.2 ...    (request, agent behavior, the evidence the reply does not show)

---

## 3. ... ## 10.          (one concept per numbered section, `### N.N` subsections)

## N. <Hand calculation, e.g. "The 30 cases, by hand">
### N.1 Worked example, <what>   ("Worked example" in the h3 makes it a tinted panel)

---

## N+1. Design review
### Q1 – <question>?       (en dash after Qn: each becomes a collapsible question)
<model answer>

---

## Key Takeaways           (one bold-lead bullet per section, nothing new)
## Check Yourself          (numbered questions, each ending in a **bold answer**: hidden on the page)
## Memory card             (term table, **Rules of thumb.**, **Next week.**)
## References              (folded on the page)

---

**Next:** [Week XX+1 theory: ...](...) · **Previous:** [Week XX-1 theory: ...](...)
```

Conventions inside sections:

- Start a section that introduces vocabulary with "New terms for this section:" and a bullet list of `**Term**: definition`.
- Precede every Mermaid diagram with a sentence that starts "This diagram shows". Aim for 2-3 diagrams per page. Validate each with the pinned Mermaid (`mermaid@11.17.2`) and confirm it draws when scrolled into view, because the site loads diagrams lazily.
- Prefer comparison tables whose left column is the reader's worry and whose right columns name the check, the mechanism or the control.
- Use bold lead-in bullets (`- **Claim.** reason`) for parallel points, and numbered steps for calculations.
- Put a trap or warning in a blockquote that starts `> **Watch out.**` (rendered as a warning callout). Other blockquotes render as notes.
- Number sections and subsections (`## 4.`, `### 4.1`), with `---` between sections. Headings are noun phrases.
- Set the `◷` read time from the site formula (230 words a minute on the rendered article), not by estimate.
- No commands anywhere in the theory file. After writing it, run `python3 tools/build_html.py` to render `<week>-theory.html`.

## Hands-on file: `handson/<week>-handson.md`

# Week XX hands-on: [Precise topic]

One line linking back to the theory file and saying what this file holds.

## 1. Lab
- `### Files`: the week's tree (README, theory/, handson/, dataset/) plus any course-root files used
- Setup and dependencies
- Full learning-friendly runnable code walkthrough (mock by default), with `lab.py` in `handson/`
- Commands and real outputs (explicitly mark simulated or illustrative ones)
- Positive / negative / adversarial scenarios as exercises
- How to interpret failed tests

## 2. Two debugging drills
- Broken input or change
- Symptoms and failed assertion
- Diagnosis steps
- Fix and verify

## 3. Completion criteria
- Checkbox acceptance tests with concrete evidence

## 4. Solutions / answer key
- Explain expected behavior without hand-waving
- Where useful, show exact test assertions
- Point to the theory file's design review (`#NN-design-review`) for the model answers

## Hands-on notebook: `handson/<week>-handson.ipynb`

Follows the `format-notebook` contract. Cells, in order:

1. Title: `# <emoji> Week XX hands-on: [Precise topic]`, Learning Objectives (3–5, one per Part), Where this fits (names the theory and hands-on files), Prerequisites (course `.venv` as kernel, which keys are needed, if any).
2. `## 📦 Step 1: Environment Setup`: stdlib imports, course-root lookup, shared imports, the week's path constants, then `✅ Environment ready`.
3. One `## <emoji> Part N` per objective: a short explanation, the `lab.py` functions copied unchanged with a demo run, then a markdown cell that reads the output.
4. A "your own cases" cell the learner edits, then both debugging drills as cells that break, show the symptom and fix.
5. Live or paid work, if any, in one `skip-execution` cell guarded by `RUN_LIVE = False`.
6. `## 📝 Summary`: one takeaway block per Part and Next Steps naming next week's notebook file.

## Week README: `README.md`

A table of the three folders in reading order (theory with its HTML, handson with its notebook, dataset) with links, then the run commands and the test count.

## Dataset README: `dataset/README.md`

A table of every file in `dataset/` with what it is and where it came from, a field table for any case file, the course-root data the week reads, and a clear marker on anything that is mock, example or otherwise not real evidence.
