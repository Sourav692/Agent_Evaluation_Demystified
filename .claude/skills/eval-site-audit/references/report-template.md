# Audit report template

Write `.website_spec/site-audits/<YYYY-MM-DD>/report.md` with exactly these sections, in this order. Most numbers come straight from `score-summary.md` (written by `score.py report`); copy them rather than recomputing. Lead every section with its point, keep sentences short, and give a URL for every finding.

```markdown
# Agent Evaluation Demystified — site audit <YYYY-MM-DD>

Site: <URL> · Deployed commit: <short SHA from `git log -1 origin/main`> · Previous audit: <date or "first audit"> · Auditor: <name>

## Verdict
<2–4 sentences: overall score (and change), the biggest strength, the biggest
remaining problem, and whether the site is ready to share publicly.>

## Scores
<the dimension table from score-summary.md: score, previous, change, target>
<one line: content X, structure Y, overall Z, and rank among the benchmarked sites>
<one line per dimension: which check IDs set or moved it>

## Check pass rate
<the by-lens table from score-summary.md and the pass/partial/fail counts>

## Fixed since last audit
<from score-summary.md "Fixed" and "Improved", grouped by lens, with evidence.
First audit: omit this section.>

## Regressions
<every regressed check, with URL evidence and the likely cause (name the commit if
you can). Say "None" if none. First audit: omit.>

## New issues
<problems found this time that no check covered; give each a proposed new check ID
and add it to data/checks.json>

## Still open — top 10 next fixes
| # | Check | Fix (file to edit: docs/… or site/build.py) | Why it matters | Effort (S/M/L) |
<ranked by severity, then by how many dimensions they move, then by effort>

## Gap register
<the gap table from score-summary.md: C1–C4 and S1–S4 with status>

## Production readiness
<PR checks as a short list: pass / partial / fail / not checked>

## Owner to confirm
<checks only the owner can settle — PR-14 (permission to reuse the OpenAI guide,
the FDE playbook and DeepLearning.AI x Arize material) and the targets in
data/start.json on the first audit — with the exact question to answer>

## Competitors
<"Benchmarked <date>" with the all-sites table, or "Carried forward from <date>">

## Method and limits
<pages crawled, pages read, browser checks done, repo gates run and their exit
codes, checks not_checked and why, any scan suggestion you overruled and why>
```

Name fixes by where they are made. Most site-wide fixes (meta tags, canonical, share image, footer, 404, sitemap, robots, edit links) are one change to the `shell()` template or the build in `site/build.py`; content fixes are in the Markdown under `docs/` (canonical — never `site/dist/`); copied pages are edited in their own `.html` under `docs/`.

## Delivering it

In this order, so the history entry carries the final record:

1. Keep `report.md`, `scores.json`, `score-summary.md`, `scan-summary.md`, `scan-checks.json` and any screenshots together in the dated folder; that folder is the audit record.
2. If the Claude Docs connector is available, publish the report as a Claude Doc and put the link in `scores.json` → `docs`.
3. Run `score.py report ... --append` to add the audit to the history.
4. In chat, give the verdict, the overall score (with its change after the first audit), and the top three next fixes; link the report rather than pasting it.
