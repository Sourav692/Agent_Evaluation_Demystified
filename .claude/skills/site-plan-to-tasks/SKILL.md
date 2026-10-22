---
name: site-plan-to-tasks
description: Review an implementation plan produced by the site-plan skill, check it for gaps and broken structure, then turn it into ready-to-build task cards grouped by phase, with a dependency-ordered board. Use this whenever the user wants to check, audit, validate or review an implementation plan, break a plan into tasks, tickets, issues or a backlog, "make tasks from the plan", "what do I build first", or plan sprint work from docs/implementation-plan.md or any similar sectioned plan, even if they do not name either skill.
---

# Plan to Tasks

Your job has two halves. First, act as the reviewer the plan never had: catch what would block or mislead a builder. Second, act as the tech lead who turns the approved plan into task cards a developer can pick up cold, without re-reading the whole plan.

The cards are only as good as the plan underneath. So check first, and do not paper over a broken plan by inventing detail in the cards.

## Step 1: Find the plan

Use the path the user gave. Otherwise look for `implementation-plan*.md` in `docs/`, `plans/`, `specs/`, `.website_spec/` and the project root. If several exist, pick the newest and say which. If none exist, stop and suggest running the site-plan skill first.

Read the whole plan. You need the context of sections 3 to 13 to write good cards, not just the task tables.

## Step 2: Run the structural check

```bash
python3 <this-skill-dir>/scripts/check_plan.py <plan.md>          # readable summary
python3 <this-skill-dir>/scripts/check_plan.py <plan.md> --json   # data for card generation
```

The script parses the plan's task tables (`| ID | Outcome | Size | Depends on |`), phases (`### Phase N: name` with a `Tasks:` line and exit-criteria bullets) and traceability table. It reports:

- **Errors** (block card generation): missing sections, duplicate or unknown task IDs, sizes other than S/M/L, dependency cycles, a task depending on one in a later phase, phases with no tasks, traceability rows pointing at missing tasks.
- **Warnings** (review, may proceed): sections 3 to 13 missing one of Goal / Decisions / Tasks / Acceptance criteria, vague task outcomes, tasks in no phase, phases without exit criteria, requirements with no task.

It also returns `build_order`, a dependency-respecting order for all tasks. Use it rather than re-deriving order by hand; that is exactly the kind of thing that goes wrong when done mentally across 60 tasks.

## Step 3: Review with judgment

The script checks shape, not sense. Read the plan as a builder and look for:

- **Missing tasks.** A decision with no task that implements it (for example, a dark theme decided in section 6 but no `DS-` task builds it). Acceptance criteria no task would satisfy.
- **Hidden dependencies.** A frontend task that obviously needs an API task but does not list it. Design-system tokens that components depend on.
- **Untestable acceptance criteria.** "Looks good", "fast", "accessible" without a measure.
- **Phase 1 bloat.** Phase 1 should deliver the top user jobs from section 3 and nothing more. Flag tasks that could move later.
- **Unresolved open questions** in section 15 that block a Phase 1 task.
- **Mismatch with the codebase.** If code exists, spot-check that paths, components and routes named in the plan are real.

Write the findings to `<tasks-dir>/PLAN_REVIEW.md`:

```markdown
# Plan review: <plan file>

Date: <today>. Verdict: Ready | Ready with fixes | Not ready

## Blocking (fix before building)
- [ ] finding, with section or task ID, and the suggested fix

## Should fix
- [ ] ...

## Notes
- ...

## Structural check
<paste the script's summary output>
```

**If there are blocking findings or script errors**, stop after writing the review. Show the user the blocking items and ask whether to fix the plan first (you can edit it if they agree) or generate cards anyway with the problems flagged. Do not quietly "fix" the plan inside the cards, because the plan would then drift from what is being built.

## Step 4: Generate task cards

Put tasks next to the plan: `<plan-dir>/tasks/` unless the user names another place. If the folder already has cards, ask before overwriting; offer to regenerate only cards whose plan rows changed.

Layout:

```
tasks/
  README.md              board: phases, build order, status
  PLAN_REVIEW.md         from step 3
  phase-1/
    01-FE-01-app-shell-and-layout.md
    02-DS-01-color-and-type-tokens.md
  phase-2/
    ...
  backlog/               tasks in no phase
```

The numeric prefix is the task's position in `build_order` within its phase, so `ls` shows a valid order to work in.

Each card follows `references/task-card-template.md`. Read it now. The card must be self-contained: pull in the relevant decision, design values, route, data shape and acceptance criteria from the plan sections the task came from, and cite the plan section so the reader can check the source. A developer should not have to open the plan to start.

Rules for cards:

- **Copy, do not invent.** Context, values and acceptance criteria come from the plan. If the plan is silent on something the task needs, write it under "Open questions" on the card, not as a made-up spec.
- **Acceptance criteria are checkable.** Start from the plan's section criteria that apply to this task, then add the task's own outcome as a criterion. Include accessibility criteria for any UI task.
- **Definition of done** is the same short checklist on every card (see template) so reviews are consistent.
- **Files likely touched** comes from the codebase when it exists (search for the real paths); otherwise from the plan's folder structure in section 8. Mark guesses.
- **Keep L tasks honest.** If while writing a card you see an L task is really two pieces of work, note "Consider splitting" with the proposed split; do not split it silently, since IDs are referenced elsewhere.

## Step 5: Write the board

`tasks/README.md`:

```markdown
# Tasks: <project>

Source plan: <path> · Review verdict: <verdict> · Generated: <date>

## Phase 1: <name>
Outcome: <phase outcome>

| # | Task | Outcome | Size | Depends on | Status |
|---|---|---|---|---|---|
| 1 | [FE-01](phase-1/01-FE-01-....md) | ... | M | - | todo |

Exit criteria:
- [ ] ...

## Critical path
<the longest dependency chain by size, S=0.5, M=1.5, L=4 days, and which tasks can run in parallel>

## Backlog
...
```

Compute the critical path from the dependency graph using those size weights; state that it is an estimate.

## Step 6: Report

Tell the user briefly: review verdict, number of blocking and should-fix findings, task and phase counts, where the folder is, and the first three tasks to start. Do not paste cards into chat.

## Optional exports

Only when the user asks, since these publish outside the repo or change shared state:

- **GitHub issues:** one issue per card via `gh issue create`, title `<ID>: <outcome>`, body from the card, labels for phase and prefix. Confirm the repo and count before creating.
- **Claude Code task list:** load the task tools and create one task per Phase 1 card, in build order.
