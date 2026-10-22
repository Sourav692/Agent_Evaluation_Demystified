# Audit report template

Write `.website_spec/site-audits/<YYYY-MM-DD>/report.md` with exactly these sections, in this order. Most numbers come straight from `score-summary.md` (written by `score.py report`); copy them rather than recomputing. Lead every section with its point, keep sentences short, and give a URL for every finding.

```markdown
# Forward Deployed — site audit <YYYY-MM-DD>

Site: <URL> · Previous audit: <date> · Auditor: <name>

## Verdict
<2–4 sentences: overall score and change, the biggest improvement, the biggest
remaining problem, and whether the site is ready to promote publicly.>

## Scores
<the dimension table from score-summary.md: score, previous, change, target>
<one line: content X (rank n of 7), structure Y (rank), overall Z (rank)>
<one line per dimension that moved: which check IDs moved it>

## Check pass rate
<the by-lens table from score-summary.md and the pass/partial/fail counts>

## Fixed since last audit
<from score-summary.md "Fixed" and "Improved", grouped by lens, with evidence>

## Regressions
<every regressed check, with URL evidence and the likely cause. Say "None" if none.>

## New issues
<problems found this time that no check covered; give each a proposed new check ID
and add it to <profile>/data/checks.json>

## Still open — top 10 next fixes
| # | Check | Fix | Why it matters | Effort (S/M/L) |
<ranked by severity, then by how many dimensions they move, then by effort>

## Gap register
<the gap table from score-summary.md: C1–C9 and S1–S6 with status>

## Production readiness
<PR checks as a short list: pass / partial / fail / not checked>

## Owner to confirm
<checks only the owner can settle, e.g. PR-14 content rights and PR-19 monitoring,
with the exact question to answer>

## Competitors
<"Carried forward from <date>" or what changed after re-benchmarking>

## Method and limits
<pages crawled, pages read, browser checks done, checks not_checked and why,
any scan suggestion you overruled and why>
```

## Delivering it

In this order, so the history entry carries the final record:

1. Keep `report.md`, `scores.json`, `score-summary.md`, `scan-summary.md`, `scan-checks.json` and any screenshots together in the dated folder; that folder is the audit record.
2. If the Claude Docs connector is available, publish the report as a Claude Doc (earlier audits live there; links in `<profile>/references/baseline-2026-10-09.md`) and put the link in `scores.json` → `docs`.
3. Run `<skill>/scripts/score.py --profile fde report ... --append` to add the audit to the history.
4. In chat, give the verdict, the overall score with its change, and the top three next fixes; link the report rather than pasting it.
