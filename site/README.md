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

`build.py` sorts every file under `docs/` into exactly one of three buckets, and
**prints all three on every build** so an omission is never silent:

| Bucket | Meaning |
|---|---|
| **Rendered** | A `.md` with unique content. Becomes one page with the shared shell and nav |
| **Copied** | A standalone `.html` that already exists under `docs/`. These are interactive — the drill scores you, the labs recompute — and could not be produced from Markdown. Their links are rewritten for the flat layout |
| **Skipped** | Left out on purpose, with the reason recorded in `SKIP` and shown on the site's own index page |

A file that is in none of the three is a build error waiting to happen, so there is
a completeness check: every tracked file under `docs/` must appear in one bucket.

## Why things are skipped

Two kinds, both measured rather than assumed.

- **`openai-eval-guide-tutorial.md`** — 87.7% phrase-identical to its own `.html`,
  which ships instead. Carrying both would put the same seven chapters on the site
  twice.
- **The six folder READMEs** — navigation, not content. Their job is done by the
  site's nav. `interview-prep/README.md` is additionally 16.5% the question bank and
  14.4% the drill.

The one duplication the site keeps on purpose is **the question bank and the drill**,
which are 65% identical. They are not two renderings — one is the readable reference,
the other hides every answer and scores your recall. `.github/scripts/check_drill_sync.py`
keeps them in step.

## Adding a document

Write the Markdown in `docs/`, add it to `RENDER` in `build.py` with a slug, a nav
title and a one-line blurb, and rebuild. If it should not be on the site, add it to
`SKIP` with the reason — that reason is published on the index page under
*"What is deliberately not here"*.

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
