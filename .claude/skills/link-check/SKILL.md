---
name: link-check
description: Find broken relative markdown links across the repo's READMEs and docs. Use when files have been moved, renamed, or restructured, before committing a restructure, or when the user asks to check/repair cross-references or asks "are the links still good".
---

> **Paths:** `<skills-root>` means the folder that holds this skill — the parent of its base directory (e.g. `~/.claude/skills`, or a repo's `.claude/skills`). Sibling skills referenced below live there too.

# Link check

This repo's folder READMEs act as indexes and link to each other with relative paths, and
course notebooks cross-reference each other by filename. Moving or renaming a file breaks
those links silently — commits `2faa463` and `ac8c306` exist purely to repair such breakage.

This skill finds the breakage. It reads files only; it never edits.

## Run it

```bash
python3 <skills-root>/link-check/scripts/check_links.py
```

Scope it to one folder when you only touched one area:

```bash
python3 <skills-root>/link-check/scripts/check_links.py courses/02-databricks-mlflow-evals
```

Add `--html` to also check `href="..."` links and scan `.html` files (index pages).

Targets are checked **case-exactly** against the paths git knows (tracked plus untracked,
non-ignored). macOS ignores case, so `docs/x.md` "exists" locally when git has `Docs/x.md` —
and 404s on GitHub. Those are reported as `case mismatch, or not tracked by git`. Fix a folder
whose case differs only on disk with a two-step rename: `git mv Docs tmp && git mv tmp docs`.

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
- Anything under `archive/`, which records an older layout on purpose.

Propose specific edits for the rest, then let the user pick which to apply.
