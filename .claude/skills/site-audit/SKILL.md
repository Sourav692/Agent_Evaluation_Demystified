---
name: site-audit
description: Re-audit one of the owner's learning sites — the Forward Deployed FDE interview-prep site (forwarddeployedprep.com; formerly fdeprep.vercel.app and forward-deployed-sigma.vercel.app) or the Agent Evaluation Demystified site (eval-demystified.vercel.app, built from docs/ by site/build.py) — for information architecture, onboarding, first-visit experience, page quality, production readiness and content coverage; score it on a 10-dimension rubric against its competitors (Hello Interview, Aced/Exponent, ByteByteGo and other prep sites for FDE; Hamel Husain, Eugene Yan, Evidently AI, DeepEval, OpenAI and DeepLearning.AI evaluation material for eval); and track every check and score against previous audits in a history file. Use this whenever the user asks to audit, re-audit, review, score, benchmark or check production or launch readiness of the Forward Deployed / FDE prep site, the eval site, or "the website", asks how the site scores now, what is still open or fixed since the last audit, whether it is ready to launch or share, or how it compares with competitors or other evaluation guides — even if they don't say "audit".
---

> **Paths:** `<skills-root>` means the folder that holds this skill — the parent of its base directory (e.g. `~/.claude/skills`, or a repo's `.claude/skills`). Sibling skills referenced below live there too.

# Site audit

A repeatable audit of one site. Each run leaves a dated folder of evidence and one new line in a history file, so progress is measured against the first recorded audit.

Audits are only comparable if the same checks (permanent IDs), the same rubric and evidence for every failure are used each time. Everything below serves that.

`<skill>` means this skill's directory (the base directory shown when the skill loads). `<profile>` means `<skill>/profiles/<name>`, the folder of the chosen site profile. Use `python3`. Every script takes `--profile <name>`.

## 0. Pick the profile

| Profile | Site | Pick it when |
| --- | --- | --- |
| `fde` | Forward Deployed — `https://forwarddeployedprep.com` (old: fdeprep.vercel.app, forward-deployed-sigma.vercel.app) | The URL is one of those; the user says Forward Deployed, FDE prep, casebook; or the repo is the FDE prep site |
| `eval` | Agent Evaluation Demystified — `https://eval-demystified.vercel.app` | The URL is that one; the user says eval site, evaluation guide, drill, labs; or the repo has `docs/` + `site/build.py` and `.github/scripts/check_drill_sync.py` |

"The website" with no URL: decide from the current repo (its README, `site/`, existing `.website_spec/site-audits/history.jsonl` → `site`). Still unclear: ask once.

Each profile folder holds everything site-specific:

| File | Use it in |
| --- | --- |
| `<profile>/references/baseline-2026-10-09.md` (fde only) — first audit's verdict, the target structure and 12-week plan the owner agreed | Step 1, for context |
| `<profile>/crawl_inventory.py` — crawl and automated scan (fde: sitemap crawl; eval: link-following crawl) | Step 2 |
| `<profile>/references/agent-prompts.md` — three reading tracks, verifier, competitor prompt | Steps 3, 5, 6 |
| `<profile>/references/browser-checks.md` — browser steps B1–B9 with JS snippets | Step 4 |
| `<profile>/references/checks.md` (from `<profile>/data/checks.json`) — every check with last recorded results | Step 5 |
| `<profile>/references/competitors.md` — competitor URLs, scores, re-benchmark rules | Step 6 |
| `<profile>/references/rubric.md` — dimension anchors, check→dimension map, `scores.json` format, targets | Step 7 |
| `<profile>/references/report-template.md` — report sections and delivery | Step 8 |
| `<profile>/profile.json` — own-site ID, competitor names, dimension labels, bundled baseline (fde) or first-audit defaults (eval, `<profile>/data/start.json`) | read by the scripts |

Shared engine: `<skill>/scripts/score.py` (validation, averages, diffs, history; Steps 1, 7) and `<skill>/scripts/render_checks.py` (Step 5).

## Site notes

### fde — Forward Deployed

- The first audit (2026-10-09: content 6.0, structure 4.4, overall 5.2 out of 10, last of seven sites on structure) is bundled as `<profile>/data/baseline-2026-10-09.json`; `score.py seed` puts it in the history.
- The owner agreed a restructure and 12-week plan (`<profile>/references/baseline-2026-10-09.md`). Old URLs are in `<profile>/data/legacy-urls-2026-10-09.txt` (IA-11).
- If the casebook moved to URLs other than `/casebook/<slug>`, update `CASEBOOK_ITEM` in `<profile>/crawl_inventory.py` before trusting CT-01 and CT-08.

### eval — Agent Evaluation Demystified (read before judging anything)

- **No audit was bundled**: on an empty history the first run sets the baseline and benchmarks the competitors; `score.py new` takes the site and targets from `<profile>/data/start.json`.
- `docs/` Markdown is canonical; `site/build.py` renders it into `site/dist/` (gitignored). A push to `main` deploys to Vercel; `cleanUrls` is off, so every page is a flat `/<slug>.html`. Flat `.html` URLs are by design, not a legacy scheme.
- Two page families: **rendered** (from Markdown, shared `shell()` with `<header class="bar">`, prev/next chapter row, contents rail) and **copied** standalone HTML (labs, drill, study plan, tutorial, playbook, stratified reporting) with a thin `.aed-sitebar` injected. The crawler tells them apart; so must you.
- The drill and labs draw their content with JavaScript, so served HTML shows little of them; they are judged in the browser.
- Most site-wide fixes are one edit to `shell()` or `build()` in `site/build.py`. Say so in the report rather than listing 30 page edits.
- The repo already has three free docs gates: `.github/scripts/check_index_coverage.py`, `.github/scripts/check_drill_sync.py` (CT-06) and `<skills-root>/link-check/scripts/check_links.py docs`. Run them; they cost nothing. Run commands from the repo root.

## Workflow

Create a task list from these steps; a full audit takes a while and the owner may step away. Below, `H` stands for `.website_spec/site-audits/history.jsonl` and `D` for `.website_spec/site-audits/<DATE>` (both at the root of the current project/repo).

### 1. Set up

1. **Site URL**: what the user gives; else the `site` of the latest history entry; else the profile's default (fde `https://forwarddeployedprep.com`, eval `https://eval-demystified.vercel.app`). eval: a page URL (`…/index.html`) is fine; the crawler cuts it to the root.
2. **Folders**: `D/` for this audit; history at `H`.
3. **fde — seed the history**: `python3 <skill>/scripts/score.py --profile fde seed --history H` (adds the baseline if missing; safe to repeat).
   **eval — what is deployed**: `git log -1 --format='%h %s' origin/main` and `vercel ls eval-demystified` (status `● Ready`). If local `main` is ahead of what is live, say the audit covers the live site and name the commit.
4. **Start this audit's record**:
   `python3 <skill>/scripts/score.py --profile <name> new --history H --date <DATE> --out D/scores.json` (add `--site <URL>` if the site moved).
   With history it carries scores, targets and competitor dates forward and resets every check to `not_checked`, so the file only ever holds what you see today; last time's results stay in the history for comparison. With no history (eval's first audit) it takes the site and targets from the profile's start file and leaves the own-site scores `null` to fill in. (fde with no history: run `seed` first.)
5. **Context**: `python3 <skill>/scripts/score.py --profile <name> trend --history H` to see where things stood (skip on a first audit). fde: also read `<profile>/references/baseline-2026-10-09.md` if this conversation lacks it.
6. **fde — one question, only if it changes the work**: has the restructure shipped, and with which URLs? (It decides how to read IA-11 and where the casebook lives.) If the user isn't there, assume nothing changed and say so in the report.

### 2. Crawl and scan

```bash
# fde
python3 <profile>/crawl_inventory.py --base <URL> --out D --legacy <profile>/data/legacy-urls-2026-10-09.txt
# eval
python3 <profile>/crawl_inventory.py --base https://eval-demystified.vercel.app --out D
```

Writes `inventory.json`, `scan-checks.json` (suggested status and evidence for about 36–40 checks), `scan-summary.md`, and `redirects.json` (with `--legacy`). A recorded audit needs the full crawl; `--limit` is for a quick look only.

- fde reads the sitemap. eval has no sitemap, so its crawler follows links breadth first from the index (and adds sitemap URLs if one appears); `inventory.json` gives each page a `kind` (home, explainer, lab, doc, standalone) plus who links to what. eval: add `--legacy <file of retired paths>` once a page has been renamed or removed (IA-09), and `--old-host eval-demystified.vercel.app` after a move to a custom domain (PR-01).
- Exit 3: the site isn't reachable or returns 401/403/5xx (deployment protection, firewall, no internet in this shell). Use WebFetch for `/sitemap.xml` (fde) or the index (eval), the hubs and a sample of pages instead, and record scan-only checks you couldn't do as `not_checked`.
- Exit 4: most pages failed; read `inventory.json` for the statuses before going on.
- eval: then run the three free repo gates in the site notes and note their exit codes (CT-06 is decided by `check_drill_sync.py`).

The scan suggests; it doesn't decide. Regex can't tell a lesson about `.md` files from a leaked file path, and anything drawn by JavaScript is invisible to it. eval soft spots: "TODO" can be content (the tutorial lists "21 TODOs"); a retired API may be named on purpose to warn against it; reading time and word counts miss anything drawn by JavaScript.

### 3. Read pages with parallel subagents

Launch Tracks A, B and C from `<profile>/references/agent-prompts.md` in one message. Build each track's URL list from this audit's `inventory.json` (the structure may have changed), starting from the lists in the prompts. Each track returns a result line per check ID.

### 4. Browser checks

Run B1–B9 in `<profile>/references/browser-checks.md` with Claude in Chrome. They decide checks served HTML can't (fde: FV-01, FV-06, ON-08, PQ-13, PQ-14, PR-04, PR-07, PR-11, PR-12, PR-17 and more; eval: FV-01 to FV-03, ON-01, IA-10, PQ-02, PQ-09, PR-04, PR-07, PR-11, PR-12, PR-16, PR-17). **Never clear the site's localStorage**: on fde it holds the owner's saved answers; on eval the drill keeps the owner's ratings under `evalround.v1`. No browser available: mark those checks `not_checked`.

### 5. Verify, then record every check

Confirm a fail before recording it when it is surprising, decides a score, or contradicts the last audit — in the browser, or with the verifier prompt. fde's first audit had two false positives from page-text reading (the 404 page and diagrams) that only the browser caught. When sources disagree: browser over reading, reading over scan.

Record every check in `scores.json` → `checks` as `pass`, `partial`, `fail`, `na` or `not_checked`, with evidence (URL plus a quote or count) for anything not passing and a short reason for `na` or `not_checked`. Checks that need the owner — record what they've told you, otherwise `not_checked`, and list them under "Owner to confirm" in the report:
- fde: PR-14 (content rights) and PR-19 (monitoring).
- eval: PR-14 (permission to reuse third-party material).

A problem no check covers: add a check to `<profile>/data/checks.json` with the next free ID in its lens, run `python3 <skill>/scripts/render_checks.py --profile <name> --history H`, then record it. IDs are never renumbered, reused or deleted. (Without `--history`, render_checks fills the Last audit columns from the bundled baseline for fde, or leaves them empty for eval.)

### 6. Competitors

- First audit (eval, empty history): benchmark all six in `<profile>/references/competitors.md` and add their scores to `scores.json` with `scores_as_of` set to today.
- Otherwise: carry competitor scores and their `scores_as_of` dates forward unless the last benchmark is over 90 days old or the user asks. To re-benchmark, follow `<profile>/references/competitors.md`.

### 7. Score

Score the ten own-site dimensions using `<profile>/references/rubric.md` and give the reason with check IDs in `rationale`. First audit: from the anchors. Later audits: start from the previous score and move it only when checks mapped to that dimension moved (or new evidence appeared). Then:

```bash
python3 <skill>/scripts/score.py --profile <name> report --scores D/scores.json --history H --out D/score-summary.md
```

It refuses incomplete files (null or missing dimensions, unrecorded checks, invalid statuses, fails without evidence). Fix the file rather than forcing it. From the second audit on, describe progress with the like-for-like pass rate (checks assessed in both audits), since the plain pass rate also moves when fewer checks were assessed.

### 8. Report, then record

1. Write `D/report.md` from `<profile>/references/report-template.md`, using the numbers in `score-summary.md`. fde: say whether the site is ahead of or behind the 12-week plan. eval: say how far each dimension is from its target.
2. If the Claude Docs connector is available, publish the report as a doc and put its link in `scores.json` → `docs`.
3. Add the audit to the history: re-run the step 7 command with `--append`. It refuses a date already in the history; use `--replace` only to redo today's audit on purpose.
4. In chat: the verdict, overall score (and its change), the top three next fixes, and the report link.

Auditing changes nothing on the site. eval: fixing findings means editing `docs/` or `site/build.py`, then following the website steps in the repo's CLAUDE.md — and pushing to `main` publishes, so ask first.

## Two rules that matter most

- **Evidence or it didn't happen.** Every `fail` and `partial` carries a URL and a quote or count, so the next audit can re-check it in minutes.
- **Protect the core.** Any regression in these is the report's first finding:
  - fde: CT-08 (the 33-design casebook) and CT-09 (the write-first worksheet loop) — what the site does better than every competitor.
  - eval: CT-02 (all eleven roadmap explainers), CT-05 (the six interactive labs) and FV-03 (the drill works) — what this site has that blog posts and docs don't.

## Examples

fde: "I merged the casebook hubs and added an About page — re-audit the site?" → Seed and copy the record; the crawl shows 12 old case URLs returning 404 (IA-11 fail, newly assessed); Track B confirms one casebook hub (IA-02 pass); browser checks pass PR-05. Navigation 3 → 5, credibility 3 → 5, overall 5.2 → 5.6. Report lead: "The casebook merge worked, but 12 old case URLs now 404 — add redirects before sharing the site."

eval: "I added share images and an edit-on-GitHub link to the shell — re-audit the site?" → `score.py --profile eval new` carries the last scores; the crawl shows og:image on 30 of 30 pages (PR-02 pass) and edit links on 29 of 29 (PR-06 pass) but two links still point at a slug renamed in the same commit (IA-03 fail; IA-09 now applies, so rerun with `--legacy`). Polish 3 → 5, overall up 0.2. Report lead: "Share previews and edit links landed site-wide; a renamed page broke two links and its old URL now 404s — add a redirect in `vercel.json`."
