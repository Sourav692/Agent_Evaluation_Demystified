# Task Card Template

One file per task. File name: `NN-<ID>-<short-slug>.md`. Replace guidance with content; drop a section only if it truly does not apply (and then write "None").

```markdown
# <ID>: <outcome, as written in the plan>

| Phase | Size | Depends on | Unblocks | Plan source |
|---|---|---|---|---|
| 1: <name> | M | FE-01, DS-02 | FE-07 | §8 Frontend architecture |

## Why
One to three sentences: which user job or success metric (plan §3) this serves, and what breaks without it.

## Context from the plan
Only what this task needs, copied or tightly summarised, each with its section:
- Decision: <decision> (§8). Rejected: <alternative>.
- Design values: tokens, breakpoints, spacing, motion (§6).
- Route, data shape or endpoint contract (§4, §9).
- Requirements covered: R3, R7 (§16).

## Scope
In:
- concrete piece of work
Out:
- what a reader might assume is included but is not (and which task owns it)

## Files likely touched
- `path/to/file` (exists | new | guess)

## Implementation notes
Ordered steps or approach hints a competent developer would want. Point to existing code patterns to follow. No speculative design beyond the plan.

## Acceptance criteria
- [ ] Checkable statement from the plan's section criteria
- [ ] The task's own outcome, phrased as a check
- [ ] UI tasks: keyboard reachable, visible focus, labelled controls, contrast meets AA, works at 320 px width and 200% zoom
- [ ] States covered where data is shown: loading, empty, error

## Test plan
Which layer proves each criterion: unit, component, end-to-end, visual or manual check, with the command if known.

## Definition of done
- [ ] Acceptance criteria all checked
- [ ] Tests added or updated, CI green
- [ ] Lint and typecheck pass
- [ ] Reviewed in a preview deployment (UI tasks)
- [ ] Plan or docs updated if a decision changed

## Open questions
- Anything the plan does not answer that this task needs. Link to plan §15 item if one exists.
```
