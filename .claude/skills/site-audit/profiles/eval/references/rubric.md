# Scoring rubric

Ten dimensions, each scored 1–10, from the point of view of one reader: **an engineer who has to evaluate a RAG system or agent at work, or answer for it in an eval-heavy interview round**. Content and structure scores are plain averages of their five dimensions; overall is the average of the two. `<skill>/scripts/score.py` does the arithmetic — never compute averages by hand.

The dimension keys are shared with the history file and must not be renamed; their meaning for this site is defined here.

## Contents

1. How to score
2. Content dimensions with anchors
3. Structure dimensions with anchors
4. Which checks inform which dimension
5. scores.json format
6. Targets

## 1. How to score

1. Record every check first (`<profile>/references/checks.md`). Scores follow the evidence, not the other way round.
2. For each dimension, read its anchors and pick the closest. Use the in-between numbers when the site sits between two anchors.
3. **First audit:** score from the anchors alone and justify each number in `rationale` with check IDs. **Later audits:** start from the previous score and move it only when a mapped check moved or new evidence appeared; name the check IDs.
4. A single fixed check rarely moves a dimension more than 1–2 points. A jump of 3+ needs several mapped checks to have moved; say which.
5. Competitor scores change only after re-benchmarking (`<profile>/references/competitors.md`). Otherwise carry them forward with their `scores_as_of` date.
6. When unsure between two numbers, take the lower one and say why.

## 2. Content dimensions

### coverage — Evaluation coverage
How much of the evaluation surface the site teaches: retrieval, generation, tool use, trajectory, multi-turn, judges, human labels, statistics, release gates, online evaluation, safety, and the organisational side (sign-off, cost, ownership).
- **2** One or two surfaces, e.g. RAG metrics only
- **5** Most single-turn surfaces; agents, statistics or production thin or missing
- **8** Every surface above has a substantive page, offline and online
- **10** All of 8, plus the organisational and production side at a level a practitioner can run with

### depth — Explanation depth
Whether pages explain *why* a metric behaves as it does, not only how to compute it.
- **2** Definitions and link lists
- **5** Explanations with some examples; few failure modes or trade-offs
- **8** Worked examples with real numbers, named failure modes ("faithful and wrong"), trade-offs between metrics
- **10** All of 8 on every page, with misconceptions called out and decision rules a reader can apply

### practice — Practice and feedback
Whether the reader does something and finds out if they got it right.
- **2** Reading only
- **5** Self-check questions with answers in plain view
- **8** Interactive labs that move real metrics, a drill that hides answers and tracks recall, self-checks with hidden answers
- **10** All of 8, plus exercises on the reader's own traces or data with feedback

### grounding — Hands-on grounding
How directly the prose is tied to code the reader can run, on current library versions.
- **2** No code, no links to notebooks
- **5** Some code or notebook links; APIs partly stale
- **8** Every explainer links to its notebook or lab; DeepEval, RAGAS, MLflow and Phoenix shown in code matching the pinned versions
- **10** All of 8, plus copy-paste snippets that run as shown and a stated "last verified against" version

### credibility — Credibility and freshness
- **2** Anonymous, undated, sources unclear
- **5** Sources cited, no maintainer identity or dates
- **8** Named maintainer with relevant background, dates on pages, third-party material credited and cleared
- **10** All of 8, plus a public changelog and visible social proof (stars, citations, testimonials)

## 3. Structure dimensions

### navigation — Navigation and IA
- **2** Orphan pages, broken links, overlapping pages with no explanation
- **5** Everything reachable from the index; sequences or cross-links partial; deliberate duplicates unexplained
- **8** 4–6 nav sections, prev/next on every sequence, theory linked to practice both ways, one name per thing
- **10** All of 8, plus redirects for every retired URL

### onboarding — Onboarding
- **2** No stated audience or first step; several start pages that disagree
- **5** An index with sections, but no single recommended first step, or start pages that disagree on order or time
- **8** Audience and one primary first step above the fold; roadmap, study plan and Level 0 agree; an interview-this-week lane
- **10** All of 8, plus a short self-assessment that points each reader to the right level

### template — Page template
Two page families exist by construction (rendered from Markdown, copied standalone HTML); this dimension asks whether a reader can tell.
- **2** Pages of the same kind look and behave differently; some lack the site nav
- **5** One shell for rendered pages; copied pages carry a bar but look different; long pages without contents
- **8** Both families share header, type and colour; explainers follow one house format; long pages have contents; diagrams render
- **10** All of 8, plus every table and diagram fits at phone width

### progress — Findability and progress
- **2** No search, no saved state
- **5** Drill saves recall ratings; no site search
- **8** Site search, drill progress that persists and resets safely, filters on long lists (question bank, drill)
- **10** All of 8, plus progress across the roadmap levels

### polish — Polish and trust
- **2** Build internals on pages, no share previews, default 404, no favicon
- **5** Clean pages and working links, but launch layer missing (share image, canonical, sitemap, 404)
- **8** Share images, canonical tags, sitemap and robots, custom 404, favicon, feedback links, no build artefacts
- **10** All of 8, plus custom domain, Lighthouse 90+, structured data, security headers, pinned scripts

## 4. Which checks inform which dimension

| Dimension | Checks |
| --- | --- |
| coverage | FV-05, CT-01, CT-02, CT-11 |
| depth | CT-07, CT-08 |
| practice | FV-02, FV-03, CT-05, CT-06, CT-09 |
| grounding | CT-03, CT-04, CT-10 |
| credibility | PQ-10, PQ-11, PR-05, PR-14, PR-15 |
| navigation | IA-01 to IA-09 |
| onboarding | ON-01 to ON-06 |
| template | FV-01, PQ-01 to PQ-05, PQ-09 |
| progress | IA-10, PR-16 |
| polish | FV-04, FV-06, PQ-06 to PQ-08, PR-01 to PR-04, PR-06 to PR-13, PR-17 to PR-19 |

This table is a guide. If you add a check, its `dimension` field in `<profile>/data/checks.json` is the source of truth.

## 5. scores.json format

One file per audit at `.website_spec/site-audits/<YYYY-MM-DD>/scores.json`, created by `<skill>/scripts/score.py --profile eval new`. On the first audit the own-site scores start as `null` and competitors are absent; `score.py report` refuses the file until every own-site dimension holds a number and each competitor you add has all ten.

```json
{
  "date": "2026-10-14",
  "site": "https://eval-demystified.vercel.app",
  "auditor": "Claude",
  "notes": "What was in scope, what was skipped and why",
  "scores": {
    "eval-demystified": {"coverage": 8, "depth": 8, "practice": 7, "grounding": 6, "credibility": 3,
                         "navigation": 7, "onboarding": 5, "template": 6, "progress": 4, "polish": 3},
    "hamel-evals": {"...": "added after benchmarking; carried forward after that"}
  },
  "scores_as_of": {"hamel-evals": "2026-10-14"},
  "targets": {"coverage": 9, "depth": 8, "practice": 8, "grounding": 8, "credibility": 7,
              "navigation": 8, "onboarding": 8, "template": 8, "progress": 6, "polish": 8},
  "rationale": {"grounding": "6: CT-03 partial (9 of 11 explainers link code), CT-04 fail (no RAGAS/MLflow/Phoenix code)"},
  "checks": {
    "IA-01": {"status": "pass", "evidence": "5 nav items: Theory, Interview prep, Audits, Interactive labs, Roadmap explainers"},
    "PR-17": {"status": "not_checked", "evidence": "Lighthouse not available in this session"}
  }
}
```

Rules `score.py report` enforces:
- every dimension present and 1–10 for every site
- every catalogue check recorded (use `not_checked` rather than leaving one out)
- `fail` and `partial` need evidence
- no check IDs outside the catalogue

## 6. Targets

Provisional, in `<profile>/data/start.json`; the owner should confirm them. They are carried forward into every audit's `targets`.

| Dimension | Target | Why this level |
| --- | --- | --- |
| coverage | 9 | Breadth is the site's reason to exist |
| depth | 8 | Worked numbers and failure modes are its teaching style |
| practice | 8 | Six labs and a drill already exist |
| grounding | 8 | The repo's notebooks are the differentiator over blog posts |
| credibility | 7 | Solo project: maintainer, dates and credits, not social proof |
| navigation | 8 | |
| onboarding | 8 | |
| template | 8 | |
| progress | 6 | Static site; search and drill progress are enough |
| polish | 8 | |
