---
name: enterprise-agent-eval-prep
description: Create beginner-friendly but Staff-level theory and hands-on study materials for any week of the 16-week Enterprise RAG and Agent Evaluation roadmap. Generates clear concepts, diagrams, runnable labs, outputs, debugging and design-review exercises without fluffy writing.
---

# Enterprise Agent Evaluation Preparation

## Trigger

Use when the learner asks for a guide, lesson, notes, workshop, assignment, lab, interview module, revision card, or Staff-level evaluation design material for a week or topic from the 16-week **Enterprise RAG & Agent Evaluation** roadmap.

Examples:
- `/enterprise-agent-eval-prep week 7`
- `/enterprise-agent-eval-prep week 12 hands-on`
- `/enterprise-agent-eval-prep week 15 theory and exercises`
- `/enterprise-agent-eval-prep release gate, beginner to Staff`

This is a portable skill folder: install it under your supported assistant's skills directory and invoke by name or simply ask for a week. Slash-command registration depends on the host; this file alone cannot guarantee `/enterprise-agent-eval-prep` is a native command.

## Required source files

- Read `references/roadmap.md` to find the exact week, learning goal, prerequisites, outputs and target tests.
- Read `references/no-ai-slop/SKILL.md` and `references/writing-standard.md` before creating or revising content. Apply both to lessons, Markdown, HTML, and explanatory code comments. Use `references/no-ai-slop/eval.md` for the final editorial check.
- Read `references/guide-template.md` to choose the required sections and the week folder layout.
- When useful, reuse `assets/agent_eval_case.jsonl` as the initial illustrative dataset; extend it for the assigned lab.

## Generation procedure

1. **Scope.** Select the requested week or concept. Preserve continuity with the evolving customer-support refund agent. If only a topic is named, map it to the most relevant roadmap week. State assumed learner knowledge briefly.
2. **Outcomes.** Define 3–5 observable outcomes (“Implement a tool argument check”; not “Understand everything”).
3. **Teach.** Organize the lesson into clear topic sections and short paragraphs. Explain each core concept in plain English, define new terms on first use, and show how it works through the refund-agent example. Cover what it does, why and when to use it, what can fail, and how to check the result. Connect prerequisites before adding Staff-level trade-offs. Use tables or diagrams when they make the explanation easier to follow.
4. **Build.** Supply a runnable lab for the specified week: file tree, prerequisites, dependencies with versions where feasible, code in full, exact commands, sample data, and expected outputs. Put code and tests in `handson/` and the data the lab reads in `dataset/` (see Deliverable format). If a real API/model is optional, give a deterministic local/mock default and mark live integration clearly.
5. **Evaluate.** Include positive, negative, edge and adversarial cases (where relevant). Verify outcomes, tool traces, authorization and database side effects, not merely assistant text. Separate hard safety invariants from soft quality metrics.
6. **Debug.** Provide at least two broken-case drills with symptoms, likely cause, diagnosis steps and fixes. Avoid fabricated claims that code was executed; mark outputs as illustrative unless validated.
7. **Reason at Staff level.** Include 3–5 architecture/operational questions with short model answers covering trade-offs, failure modes, scale, cost, privacy and observability.
8. **Close.** Give a completion checklist, objective acceptance criteria, a one-page memory card, and the next week's dependency.
9. **Validate.** Check code paths, imports, schema/expected output consistency, diagram readability, safety boundaries and editorial quality. Confirm every concept required by the selected scope is explained, every new term is defined, and each section follows logically from the previous one. Apply the no-ai-slop checklist and fix failed checks. Do not claim tests pass unless run.

## Mode selection

- **Theory only:** sections 1–4, conceptual worked example, trade-offs, five quick questions and memory card. Skip full lab.
- **Hands-on only:** prerequisites, files, full runnable code, commands, expected output, tests, debugging, answers and criteria. Include a minimal 5-sentence conceptual primer.
- **Full guide (default):** both, as a theory file (Markdown and HTML) and a hands-on file (Markdown and notebook), with code and a Staff design review.
- **Interview module:** concise spoken explanation, one scenario, architecture, metrics, trade-offs, five interview questions with model answers, one-page memory card.

## Invariants

- Never authorize a refund through prompt instructions alone: authorization and entitlement require backend enforcement.
- Avoid real financial transactions and personal customer data: use mocks and synthetic records.
- Treat retrieval evidence and LLM judges as untrusted inputs. Prefer deterministic checks for safety/authorization/idempotency.
- A flexible correct trajectory is acceptable even if it differs from one reference ordering; require invariant steps, not arbitrary sequences.
- Always distinguish final text quality from persisted task completion and record observed vs inferred outcomes.
- Present release thresholds as illustrative until tied to actual product risk and evidence.
- Preserve pinned case, policy, prompt and model versions for comparisons.

## Deliverable format

Use Markdown headings; short paragraphs; bullets when they reduce prose; tables only for real comparisons; one consistent domain example.

For file output, every week uses the same folder layout. `<week>` is the week's folder name, such as `week-04-retrieval-evaluation`:

```text
weeks/<week>/
  README.md                  # week index: the three folders in reading order, run commands, test count
  theory/
    <week>-theory.md         # theory file, the source (sections listed in references/guide-template.md)
    <week>-theory.html       # rendered from the Markdown by tools/build_html.py; never edited by hand
  handson/
    <week>-handson.md        # hands-on file (sections listed in references/guide-template.md)
    <week>-handson.ipynb     # the same lab as a notebook, one step per cell
    lab.py                   # the week's runnable lab
    tests/test_lab.py        # acceptance tests
  dataset/
    README.md                # each file, its fields, its provenance, and the course-root data the week reads
    <data files>             # fixtures, broken copies, frozen runs, review sheets
```

Rules for the layout:

- Keep the long, unique file names (`week-04-retrieval-evaluation-theory.md`, not `theory.md`) so search results and links stay unambiguous.
- Put no commands in the theory file. Put every command, real output block, exercise, drill and solution in the hands-on file.
- Link the two files to each other at the top, and link sections across files with GitHub-style anchors (`../theory/<week>-theory.md#11-design-review`). After renumbering theory sections, update the hands-on links and the `coverage.md` rows that point at them.
- Data used by more than one week stays at the course root (`datasets/`, `shared/`). A week's `dataset/` holds only that week's data, and its README links to the root files the week reads.
- Code resolves paths from its own location: `HERE = Path(__file__).resolve().parent` is `handson/`, `HERE.parent / "dataset"` is the week's data, and `HERE.parents[2]` is the course root.
- Tests load `lab.py` by path under a unique module name (`week04_lab`), register it in `sys.modules` before executing it, and run with `--import-mode=importlib`.
- After creating a week, add it to the course README's study-order table and to `coverage.md` with "Theory §N" or "Hands-on §N" references.

Rules for the theory HTML:

- Write the theory file in the field-guide format described in `references/guide-template.md` (reference page: `docs/concepts/field-guide/02-rag-retrieval.md`). The Markdown is the source. Render it with `python3 tools/build_html.py` from `new_course/` (needs `markdown==3.7`, in `requirements-core.txt`). The builder runs the page through the same `site/build.py` transforms and site stylesheets as the published field guide: section rail, callouts, worked-example panels, table cards, collapsible design-review questions, hidden Check Yourself answers and folded references.
- Rerun it after every theory edit. `python3 tools/build_html.py --check` exits 1 when any HTML is stale, and each week's tests call the same check.

Rules for the hands-on notebook:

- Follow the `format-notebook` contract (sourav-skills plugin): title cell with 3–5 learning objectives and prerequisites, a setup cell, one Part per objective with `---` separators and one emoji per heading, `# ====` banner comments, every cell ending in a printed result, a summary cell naming the next notebook by file name, and no install cells.
- Mirror the hands-on file's lab: load the data, define the lab's functions, run them, interpret the output in a markdown cell, then a "your own cases" cell and the two drills.
- Copy every function and class from `lab.py` unchanged, ordered so each is defined before use. Code that differs from `lab.py`, such as a drill's fixed version, gets a new name (`check_forbidden_actions_fail_closed`).
- Find the course root in the setup cell so the notebook runs from its own folder or from `new_course/`: `COURSE = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "shared" / "support_agent.py").exists())`.
- Any paid or live cell gets the `skip-execution` tag, a markdown note above it with the cost and credentials, and a `RUN_LIVE = False` guard inside, so even a full Jupyter run stays free.
- Commit notebooks with outputs cleared and `execution_count` null (the repository's pre-commit hook enforces this outside course 03).
- Add three tests per week through `shared/course_checks.py`: `notebook_drift(...) == []`, `run_notebook(...)` printing the expected key results, and `html_is_fresh(...)` for the theory file. Verify once in a real kernel with `jupyter nbconvert --execute`, writing the executed copy outside the repository.

## Writing requirements

Write for a beginner learning to evaluate agents. Use a precise title, descriptive section headings, and topic subsections where needed. Keep one idea per paragraph, usually in 1–3 sentences. Use connected prose for explanations, numbered steps for procedures, and bullets for parallel items.

Keep explanations crisp by removing repetition and filler. Preserve every concept needed for the requested week or topic, including assumptions, limits, failure modes, and reasoning. Explain unfamiliar terms before using them in code, formulas, or design questions. A concise lesson must still let the learner explain the concept and apply it.

Use the bundled no-ai-slop skill for editing and its evaluation checklist for review. For generated lessons, review silently and return the requested lesson format. For explicit editing requests, follow its edited-draft and What changed format. The bundled files preserve the source skill from `/Users/sourav/.agents/skills/no-ai-slop/` so this skill remains portable.
