---
name: verify-site
description: Run the full site verification (sync, content check, lint, typecheck, build) from site/ and report failures. Use before committing or opening a PR that touches site/ or synced source content.
---

Run each step from `site/`, in order. Stop at the first failure, show the decisive error lines, and diagnose before moving on.

1. `npm run sync`: regenerates `site/content/` from root sources. If it fails reading `../08_Company_Specific_Prep/Blitzy`, the clone lacks that local-only dir; report it, don't create it.
2. `npm run check:content`: content contract (worksheet structure, editorial metadata, links, glossary, placeholders). Last known good: 85 pages, 694 links, 133 diagrams; report the new counts.
3. `npm run lint`
4. `npx tsc --noEmit`
5. `npm run build`

Then run `git status --short` and report:
- `site/content/manifest.json` modified only by `generatedAt` is expected noise from sync. Say so rather than treating it as a change.
- **Privacy check:** warn loudly if anything from `09_Study_Plans/` (purchased library index) or text copied from `99_Reference_Library/` third-party PDFs is staged, or if a newly synced page references the purchased library (`LIBRARY_MAP.md`, `ROADMAP_7_DAY.md`, the condensed plan xlsx).

Finish with a short pass/fail line per step.
