---
name: eval-site-audit
description: Audit the Agent Evaluation Demystified website (https://eval-demystified.vercel.app, built from docs/ by site/build.py) for information architecture, onboarding, first-visit experience, page quality, production readiness and content coverage; score it on a 10-dimension rubric against Hamel Husain, Eugene Yan, Evidently AI, DeepEval, OpenAI and DeepLearning.AI evaluation material; and track every check and score against previous audits in a history file. Use this whenever the user asks to audit, re-audit, review, score, benchmark or check launch readiness of the eval site or "the website", asks how the site scores now, what is still open or fixed since the last audit, whether it is ready to share, or how it compares with other evaluation guides — even if they don't say "audit".
---

# Agent Evaluation Demystified site audit

A repeatable audit of the static site this repo publishes. Each run leaves a dated folder of evidence and one new line in a history file, so progress is measured against the first recorded audit. **No audit has been recorded yet**: the first run sets the baseline and benchmarks the competitors.

Audits are only comparable if the same checks (permanent IDs), the same rubric and evidence for every failure are used each time. Everything below serves that.

`<skill>` means this skill's directory (the base directory shown when the skill loads). Run commands from the repo root. Use `python3`.

| File | Use it in |
| --- | --- |
| `scripts/crawl_inventory.py` — link-following crawl and automated scan | Step 2 |
| `references/agent-prompts.md` — three reading tracks, verifier, competitor prompt | Steps 3, 5, 6 |
| `references/browser-checks.md` — browser steps B1–B9 with JS snippets | Step 4 |
| `references/checks.md` (from `data/checks.json`) — all checks | Step 5 |
| `references/competitors.md` — competitor URLs, re-benchmark rules | Step 6 |
| `references/rubric.md` — dimension anchors, check→dimension map, `scores.json` format, targets | Step 7 |
| `scripts/score.py` — validation, averages, diffs, history | Steps 1, 7 |
| `references/report-template.md` — report sections and delivery | Step 8 |

## How this site is built (read before judging anything)

- `docs/` Markdown is canonical; `site/build.py` renders it into `site/dist/` (gitignored). A push to `main` deploys to Vercel; `cleanUrls` is off, so every page is a flat `/<slug>.html`. Flat `.html` URLs are by design, not a legacy scheme.
- Two page families: **rendered** (from Markdown, shared `shell()` with `<header class="bar">`, prev/next chapter row, contents rail) and **copied** standalone HTML (labs, drill, study plan, tutorial, playbook, stratified reporting) with a thin `.aed-sitebar` injected. The crawler tells them apart; so must you.
- The drill and labs draw their content with JavaScript, so served HTML shows little of them; they are judged in the browser.
- Most site-wide fixes are one edit to `shell()` or `build()` in `site/build.py`. Say so in the report rather than listing 30 page edits.
- The repo already has three free docs gates: `.github/scripts/check_index_coverage.py`, `.github/scripts/check_drill_sync.py` (CT-06) and `.claude/skills/link-check/scripts/check_links.py docs`. Run them; they cost nothing.

## Workflow

Create a task list from these steps; a full audit takes a while and the owner may step away.

### 1. Set up

1. **Site URL**: what the user gives; else the `site` of the latest history entry; else `https://eval-demystified.vercel.app`. A page URL (`…/index.html`) is fine: the crawler cuts it to the root.
2. **Folders**: `.website_spec/site-audits/<YYYY-MM-DD>/` at the repo root; history at `.website_spec/site-audits/history.jsonl`.
3. **What is deployed**: `git log -1 --format='%h %s' origin/main` and `vercel ls eval-demystified` (status `● Ready`). If local `main` is ahead of what is live, say the audit covers the live site and name the commit.
4. **Start this audit's record**:
   `python3 <skill>/scripts/score.py new --history .website_spec/site-audits/history.jsonl --date <DATE> --out .website_spec/site-audits/<DATE>/scores.json`
   With history it carries scores, targets and competitor dates forward and resets every check to `not_checked`. With no history (the first audit) it takes the site and targets from `data/start.json` and leaves the own-site scores `null` to fill in.
5. **Context**: `score.py trend --history .website_spec/site-audits/history.jsonl` to see where things stood (skip on the first audit).

### 2. Crawl and scan

```bash
python3 <skill>/scripts/crawl_inventory.py --base https://eval-demystified.vercel.app --out .website_spec/site-audits/<DATE>
```

The site has no sitemap, so the crawler follows links breadth first from the index (and adds sitemap URLs if one appears). Writes `inventory.json` (pages with `kind`: home, explainer, lab, doc, standalone; plus who links to what), `scan-checks.json` (suggested status and evidence for about 40 checks), and `scan-summary.md`. A recorded audit needs the full crawl; `--limit` is for a quick look only. Add `--legacy <file of retired paths>` once a page has been renamed or removed (IA-09), and `--old-host eval-demystified.vercel.app` after a move to a custom domain (PR-01).

- Exit 3: the site isn't reachable or returns 401/403/5xx (deployment protection, no internet in this shell). Use WebFetch on the index and a sample of pages instead, and record scan-only checks you couldn't do as `not_checked`.
- Exit 4: most pages failed; read `inventory.json` for the statuses before going on.

Then run the three free repo gates listed above and note their exit codes (CT-06 is decided by `check_drill_sync.py`).

The scan suggests; it doesn't decide. Known soft spots: "TODO" can be content (the tutorial lists "21 TODOs"); a retired API may be named on purpose to warn against it; reading time and word counts miss anything drawn by JavaScript.

### 3. Read pages with parallel subagents

Launch Tracks A, B and C from `references/agent-prompts.md` in one message. Build each track's URL list from this audit's `inventory.json`, starting from the lists in the prompts. Each track returns a result line per check ID.

### 4. Browser checks

Run B1–B9 in `references/browser-checks.md` with Claude in Chrome. They decide checks served HTML can't (FV-01 to FV-03, ON-01, IA-10, PQ-02, PQ-09, PR-04, PR-07, PR-11, PR-12, PR-16, PR-17). Never clear the site's localStorage: the drill keeps the owner's ratings under `evalround.v1`. No browser available: mark those checks `not_checked`.

### 5. Verify, then record every check

Confirm a fail before recording it when it is surprising, decides a score, or contradicts the last audit — in the browser, or with the verifier prompt. When sources disagree: browser over reading, reading over scan.

Record every check in `scores.json` → `checks` as `pass`, `partial`, `fail`, `na` or `not_checked`, with evidence (URL plus a quote or count) for anything not passing and a short reason for `na` or `not_checked`. PR-14 (permission to reuse third-party material) needs the owner: record what they've told you, otherwise `not_checked`, and list it under "Owner to confirm".

A problem no check covers: add a check to `data/checks.json` with the next free ID in its lens, run `python3 <skill>/scripts/render_checks.py --history .website_spec/site-audits/history.jsonl`, then record it. IDs are never renumbered, reused or deleted.

### 6. Competitors

First audit: benchmark all six in `references/competitors.md` and add their scores to `scores.json` with `scores_as_of` set to today. Later audits: carry them forward unless the last benchmark is over 90 days old or the user asks.

### 7. Score

Score the ten dimensions using `references/rubric.md` and give the reason with check IDs in `rationale`. First audit: from the anchors. Later audits: start from the previous score and move it only when mapped checks moved. Then:

```bash
python3 <skill>/scripts/score.py report --scores .website_spec/site-audits/<DATE>/scores.json \
  --history .website_spec/site-audits/history.jsonl --out .website_spec/site-audits/<DATE>/score-summary.md
```

It refuses incomplete files (null or missing dimensions, unrecorded checks, invalid statuses, fails without evidence). Fix the file rather than forcing it. From the second audit on, describe progress with the like-for-like pass rate (checks assessed in both audits).

### 8. Report, then record

1. Write `.website_spec/site-audits/<DATE>/report.md` from `references/report-template.md`, using the numbers in `score-summary.md`. Say how far each dimension is from its target.
2. If the Claude Docs connector is available, publish the report as a doc and put its link in `scores.json` → `docs`.
3. Add the audit to the history: re-run the step 7 command with `--append`. It refuses a date already in the history; use `--replace` only to redo today's audit on purpose.
4. In chat: the verdict, overall score (and change), the top three next fixes, and the report link.

Auditing changes nothing on the site. Fixing findings means editing `docs/` or `site/build.py`, then following the website steps in CLAUDE.md — and pushing to `main` publishes, so ask first.

## Two rules that matter most

- **Evidence or it didn't happen.** Every `fail` and `partial` carries a URL and a quote or count, so the next audit can re-check it in minutes.
- **Protect the core.** CT-02 (all eleven roadmap explainers), CT-05 (the six interactive labs) and FV-03 (the drill works) are what this site has that blog posts and docs don't. Any regression there is the report's first finding.

## Example

"I added share images and an edit-on-GitHub link to the shell — re-audit the site?" → `score.py new` carries the last scores; the crawl shows og:image on 30 of 30 pages (PR-02 pass) and edit links on 29 of 29 (PR-06 pass) but two links still point at a slug renamed in the same commit (IA-03 fail; IA-09 now applies, so rerun with `--legacy`). Polish 3 → 5, overall up 0.2. Report lead: "Share previews and edit links landed site-wide; a renamed page broke two links and its old URL now 404s — add a redirect in `vercel.json`."
