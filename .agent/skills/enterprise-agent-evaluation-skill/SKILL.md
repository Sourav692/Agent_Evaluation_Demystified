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
- Read `references/guide-template.md` to choose the required sections.
- When useful, reuse `assets/agent_eval_case.jsonl` as the initial illustrative dataset; extend it for the assigned lab.

## Generation procedure

1. **Scope.** Select the requested week or concept. Preserve continuity with the evolving customer-support refund agent. If only a topic is named, map it to the most relevant roadmap week. State assumed learner knowledge briefly.
2. **Outcomes.** Define 3–5 observable outcomes (“Implement a tool argument check”; not “Understand everything”).
3. **Teach.** Organize the lesson into clear topic sections and short paragraphs. Explain each core concept in plain English, define new terms on first use, and show how it works through the refund-agent example. Cover what it does, why and when to use it, what can fail, and how to check the result. Connect prerequisites before adding Staff-level trade-offs. Use tables or diagrams when they make the explanation easier to follow.
4. **Build.** Supply a runnable lab for the specified week: file tree, prerequisites, dependencies with versions where feasible, code in full, exact commands, sample fixtures, and expected outputs. If a real API/model is optional, give a deterministic local/mock default and mark live integration clearly.
5. **Evaluate.** Include positive, negative, edge and adversarial cases (where relevant). Verify outcomes, tool traces, authorization and database side effects, not merely assistant text. Separate hard safety invariants from soft quality metrics.
6. **Debug.** Provide at least two broken-case drills with symptoms, likely cause, diagnosis steps and fixes. Avoid fabricated claims that code was executed; mark outputs as illustrative unless validated.
7. **Reason at Staff level.** Include 3–5 architecture/operational questions with short model answers covering trade-offs, failure modes, scale, cost, privacy and observability.
8. **Close.** Give a completion checklist, objective acceptance criteria, a one-page memory card, and the next week's dependency.
9. **Validate.** Check code paths, imports, schema/expected output consistency, diagram readability, safety boundaries and editorial quality. Confirm every concept required by the selected scope is explained, every new term is defined, and each section follows logically from the previous one. Apply the no-ai-slop checklist and fix failed checks. Do not claim tests pass unless run.

## Mode selection

- **Theory only:** sections 1–4, conceptual worked example, trade-offs, five quick questions and memory card. Skip full lab.
- **Hands-on only:** prerequisites, files, full runnable code, commands, expected output, tests, debugging, answers and criteria. Include a minimal 5-sentence conceptual primer.
- **Full guide (default):** both, with code and a Staff design review.
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

Use Markdown headings; short paragraphs; bullets when they reduce prose; tables only for real comparisons; one consistent domain example. Provide optional Markdown/HTML exports only if requested. For file output, name `week-XX-<topic>-study-guide.md` and matching `.html`.

## Writing requirements

Write for a beginner learning to evaluate agents. Use a precise title, descriptive section headings, and topic subsections where needed. Keep one idea per paragraph, usually in 1–3 sentences. Use connected prose for explanations, numbered steps for procedures, and bullets for parallel items.

Keep explanations crisp by removing repetition and filler. Preserve every concept needed for the requested week or topic, including assumptions, limits, failure modes, and reasoning. Explain unfamiliar terms before using them in code, formulas, or design questions. A concise lesson must still let the learner explain the concept and apply it.

Use the bundled no-ai-slop skill for editing and its evaluation checklist for review. For generated lessons, review silently and return the requested lesson format. For explicit editing requests, follow its edited-draft and What changed format. The bundled files preserve the source skill from `/Users/sourav/.agents/skills/no-ai-slop/` so this skill remains portable.
