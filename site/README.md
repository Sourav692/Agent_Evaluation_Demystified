# site/

The static site, generated from the Markdown in `docs/`.

```bash
pip install -r site/requirements.txt      # markdown==3.7, nothing else
python3 site/build.py                     # writes site/dist/
python3 -m http.server -d site/dist 8000  # http://localhost:8000
```

`site/dist/` is a **build artifact and is gitignored**, like `mlruns/` and the
persisted Chroma stores. Rebuild it; never edit it.

## The one rule

**The Markdown in `docs/` is canonical.** Pages are rendered from it, so there is no
second source to drift. This repo has hit that failure three times — the question
bank against the drill, the tutorial against its page, and a prose explainer that
turned out to duplicate the tutorial and was archived. Generating rather than
hand-converting is how the site avoids being the fourth.

## What goes in, and what does not

`build.py` sorts every file under `docs/` into exactly one bucket, and
**prints them on every build** so an omission is never silent:

| Bucket | Meaning |
|---|---|
| **Rendered** | A `.md` with unique content. Becomes one page with the shared shell and nav |
| **Copied** | A standalone `.html` that already exists under `docs/`. These are interactive — the drill scores you, the labs recompute — and could not be produced from Markdown. Their links are rewritten for the flat layout |
| **Site pages** | `about.md` and `CHANGELOG.md`, listed in `SITE_PAGES`. Rendered like the first bucket, linked from the footer, never carded on the index |
| **Skipped** | Left out on purpose, with the reason recorded in `SKIP` and printed by every build |

A file in no bucket would never be published, so there is a completeness check:
every tracked file under `docs/` must appear in one bucket, or the build fails.

## Why things are skipped

`SKIP` in `build.py` is canonical; this table mirrors it. If they disagree, trust
`build.py` and fix this table.

| File under `docs/` | Why |
|---|---|
| `README.md` | Folder index. Its job is done by the site's navigation |
| `concepts/README.md` | Folder index |
| `guide-audits/README.md` | Folder index |
| `interactive-labs/README.md` | Folder index |
| `interview-prep/README.md` | Folder index, and 16.5% the question bank plus 14.4% the drill: it summarises pages the site already carries |
| `study-guide/README.md` | Folder index |

The one duplication the site keeps on purpose is **the question bank and the drill**,
which are 65% identical. They are not two renderings — one is the readable reference,
the other hides every answer and scores your recall. `.github/scripts/check_drill_sync.py`
keeps them in step.

## Adding a document

Write the Markdown in `docs/`, add it to `RENDER` in `build.py` with a slug, a nav
title and a one-line blurb, and rebuild. If it should not be on the site, add it to
`SKIP` with the reason, and add a row to the table above.

## Page dates

Every published page shows when it last changed, and the sitemap's `lastmod` reads
the same date. Vercel's build has no git history, so the dates are computed locally
by `site/stamp_dates.py` and committed as `site/page-dates.json`
(`{"docs/<path>": "YYYY-MM-DD"}`, one entry per page in `RENDER` and `COPY`).

- **The pre-commit hook stamps them.** Add this line before the hook's final
  `exec` line in `.git/hooks/pre-commit` (hooks aren't tracked, so each clone needs it):

  ```sh
  root="$(git rev-parse --show-toplevel)"
  python3 "$root/site/stamp_dates.py" --staged && git add "$root/site/page-dates.json" || exit 1
  ```

- **CI is the real control.** The docs-sync workflow runs `stamp_dates.py --check`
  and fails, naming the file, when a page's date doesn't match its last commit.
  This catches a skipped hook (`--no-verify`) or a clone without it. To fix, run
  `python3 site/stamp_dates.py` and commit the result.

## Images

`build()` copies `site/assets/` into `site/dist/assets/`. It holds the share preview
`og.png` (1200×630), `favicon.svg` (the "AE" monogram) and its 32 px fallback
`favicon-32.png`. The share preview is rendered from `site/og.html`, and the PNG
favicon from the SVG, with headless Chrome:

```sh
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless=new --hide-scrollbars --virtual-time-budget=5000 --window-size=1200,630 \
  --screenshot="$PWD/site/assets/og.png" "file://$PWD/site/og.html"
"$C" --headless=new --hide-scrollbars --default-background-color=00000000 --window-size=32,32 \
  --screenshot="$PWD/site/assets/favicon-32.png" "file://$PWD/site/assets/favicon.svg"
```

## The output check

`site/check_dist.py` runs after every build, on Vercel and in the docs-sync workflow, so a
page that breaks a rule never deploys. It checks every page in `site/dist/` for share tags,
canonical and description, exactly one `<h1>`, no `docs/…` path shown as text, no GitHub
link to a doc the site serves itself, no dead link or `#fragment`, and exact versions on
CDN URLs. Each failure prints `<file>: <rule>: <detail>`.

```sh
python3 site/check_dist.py --self-test   # each rule fires on a small broken page
python3 site/check_dist.py               # the real build
```
