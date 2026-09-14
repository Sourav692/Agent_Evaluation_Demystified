---
name: link-check
description: Find broken relative markdown links across the repo's READMEs and docs. Use when files have been moved, renamed, or restructured, before committing a restructure, or when the user asks to check/repair cross-references or asks "are the links still good".
---

# Link check

This repo's folder READMEs act as indexes and link to each other with relative paths, and
course notebooks cross-reference each other by filename. Moving or renaming a file breaks
those links silently — commits `2faa463` and `ac8c306` exist purely to repair such breakage.

This skill finds the breakage. It reads files only; it never edits.

## Run it

```bash
python3 .claude/skills/link-check/scripts/check_links.py
```

Scope it to one folder when you only touched one area:

```bash
python3 .claude/skills/link-check/scripts/check_links.py courses/02-databricks-mlflow-evals
```

The script scans every tracked `.md` file, resolves each relative link target against the
linking file's own directory, and reports targets that don't exist. It skips external URLs
(`http://`, `https://`, `mailto:`) and bare in-page anchors (`#section`). It URL-decodes
targets first, so percent-encoded paths like `Analysis%20(v2).md` resolve correctly.

Exit code is `0` when everything resolves and `1` when anything is broken, so it also works
as a pre-push gate.

## Reporting back

Group the findings by the file containing the broken links, and for each one say whether the
target looks **moved** (a file of that name exists elsewhere — give the path), **renamed**
(a close match exists in the expected directory), or **gone** (no candidate anywhere).

Two categories are expected and are NOT bugs — call them out as such rather than proposing
fixes:

- References to files left behind in the `AI-ENGINEERING-DEMYSTIFIED` monorepo
  (`NOTEBOOK_INDEX.md`, the OpenAI coverage-gap analysis, the red-teaming notebook). The root
  README documents these as mentions, not links.
- Anything under `labs/agent-evaluation/arize-phoenix-labs/`, which is third-party material
  kept verbatim.

Propose specific edits for the rest, then let the user pick which to apply.
