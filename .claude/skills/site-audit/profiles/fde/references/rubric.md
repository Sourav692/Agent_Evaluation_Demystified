# Scoring rubric

Ten dimensions, each scored 1–10, from the point of view of one reader: an engineer preparing for a Forward Deployed Engineer loop at an AI company. Content and structure scores are plain averages of their five dimensions; overall is the average of content and structure. `<skill>/scripts/score.py` does the arithmetic — never compute averages by hand.

## Contents

1. How to score
2. Content dimensions with anchors
3. Structure dimensions with anchors
4. Which checks inform which dimension
5. scores.json format
6. Baseline and targets (2026-10-09)

## 1. How to score

Scores are judgement, but anchored so two audits months apart mean the same thing.

1. Record every check first (`<profile>/references/checks.md`). Scores follow the evidence, not the other way round.
2. For each dimension, read its anchors below and pick the closest. Use the in-between numbers when the site sits between two anchors.
3. Start from the previous audit's score. Move it only when a check mapped to that dimension changed, or new evidence appeared. Write the reason in `rationale`, naming the check IDs that moved.
4. A single fixed check rarely moves a dimension more than 1–2 points. A jump of 3+ needs several mapped checks to have moved; say which.
5. Competitor scores change only after re-benchmarking them (`<profile>/references/competitors.md`). Otherwise carry them forward with their `scores_as_of` date.
6. When unsure between two numbers, take the lower one and say why. Over-scoring hides work that still needs doing.

## 2. Content dimensions

### coverage — FDE coverage
How many FDE loop rounds the site prepares you for: discovery and decomposition, AI system design, coding, behavioural, client simulation, take-home, company-specific prep.
- **2** One or two rounds, general SWE material only
- **5** Several rounds covered, two or more major rounds missing or empty
- **8** Every common round has real material; company-specific prep for a few companies
- **10** Every round, take-home and company loops for the main FDE employers, all complete

### depth — Worked-solution depth
How complete and reasoned the model answers are, especially for AI systems.
- **2** Short outlines or link lists
- **5** Some full worked answers, little on trade-offs or failure modes
- **8** Many full designs with trade-offs, failure modes, evaluation and rollout
- **10** A large casebook at several depths, each with level calibration and checked facts

### practice — Practice and feedback
Whether you produce answers and get judged on them, not only read.
- **2** Reading only
- **5** Questions with model answers, self-check only
- **8** Write-first worksheets with rubrics and timers, plus some external feedback (AI, peer or human)
- **10** Timed written and spoken practice with reliable feedback on every attempt

### grounding — Real-loop grounding
How directly the material is tied to real interviews.
- **2** No reference to real loops
- **5** General description of FDE rounds, no company detail or reported questions
- **8** Company guides with round formats and sample prompts; some reported questions
- **10** Current, candidate-reported questions and loop write-ups for the main employers, kept up to date

### credibility — Credibility and freshness
Can a reader trust it and tell it is current.
- **2** Anonymous, undated, sources unclear
- **5** Some sources or dates, no author identity
- **8** Named author with relevant background, dates on pages, sources credited, rights clear
- **10** All of 8, plus a public changelog and visible social proof

## 3. Structure dimensions

### navigation — Navigation and IA
- **2** Same content under several hubs, long nav, many numbering systems, legacy URLs
- **5** Mostly one home per content set; some duplication or inconsistent names remain
- **8** 4–6 nav items, one home per content set, one name per thing, one URL scheme
- **10** All of 8, plus redirects for every retired URL and breadcrumbs that always match the hub

### onboarding — Onboarding
- **2** No clear first step, or several pages that contradict each other
- **5** A start page exists but competes with others or contradicts their numbers
- **8** One start page, one meaning of path, consistent hours, an express lane for interview-soon users
- **10** All of 8, plus the diagnostic leads straight into a personalised plan that only uses ready material

### template — Page template
- **2** Pages of the same type look and behave differently; some sit outside the site shell
- **5** One main template with several variants and inconsistencies (labels, reading times, prev/next)
- **8** One shell with three body variants; consistent objectives, reading time, prev/next, takeaways
- **10** All of 8, plus every page within length limits and every diagram fits its column

### progress — Progress and filters
- **2** No progress, no search, no filters
- **5** Search and some progress tracking; first-visit experience shows locks or confusing states
- **8** Clear progress per section, filters with counts on list pages, nothing locked on first visit
- **10** All of 8, plus export/import of progress and resumable sessions across devices

### polish — Polish and trust
- **2** Visible build artefacts, empty sections in the nav, no share previews, no About page
- **5** Basics present (404, sitemap, robots, mobile menu) but launch layer missing
- **8** Custom domain, share images, canonical tags, analytics, About page, feedback link, no artefacts
- **10** All of 8, plus Lighthouse 90+, structured data, security headers and monitoring

## 4. Which checks inform which dimension

Each check in `<profile>/data/checks.json` has a `dimension`. Before scoring a dimension, list its checks and their movement since the last audit:

| Dimension | Checks |
| --- | --- |
| coverage | CT-03, CT-04, CT-10, FV-05 |
| depth | CT-01, CT-08 |
| practice | CT-05, CT-07, CT-09, FV-06 |
| grounding | CT-02, CT-06 |
| credibility | PQ-15, PR-05, PR-14, PR-15 |
| navigation | IA-01 to IA-13 |
| onboarding | ON-01 to ON-08 |
| template | PQ-01 to PQ-06, PQ-11 to PQ-14 |
| progress | FV-01, IA-14, PR-16 |
| polish | FV-02 to FV-04, PQ-07 to PQ-10, PR-01 to PR-04, PR-06 to PR-13, PR-17 to PR-20 |

This table is a guide. If you add a check, its `dimension` field in `<profile>/data/checks.json` is the source of truth.

## 5. scores.json format

One file per audit at `.website_spec/site-audits/<YYYY-MM-DD>/scores.json`. Create it with `python3 <skill>/scripts/score.py --profile fde new --history .website_spec/site-audits/history.jsonl --date <DATE> --out <file>`: scores, targets and competitor dates are carried forward and every check starts as `not_checked`.

```json
{
  "date": "2026-11-20",
  "site": "https://forwarddeployedprep.com",
  "auditor": "Claude",
  "notes": "What was in scope, what was skipped and why",
  "scores": {
    "forward-deployed": {"coverage": 7, "depth": 9, "practice": 7, "grounding": 4, "credibility": 6,
                          "navigation": 5, "onboarding": 7, "template": 6, "progress": 7, "polish": 7},
    "hello-interview": {"...": "carried forward unless re-benchmarked"}
  },
  "scores_as_of": {"hello-interview": "2026-10-09"},
  "targets": {"coverage": 8, "depth": 9, "practice": 8, "grounding": 7, "credibility": 8,
              "navigation": 8, "onboarding": 8, "template": 8, "progress": 8, "polish": 9},
  "rationale": {"credibility": "+3: PR-05 About page and PQ-15 dates now pass; PR-14 rights still open"},
  "checks": {
    "IA-01": {"status": "pass", "evidence": "5 nav items: Start, Learn, Casebook, Practice, Final Week"},
    "PR-17": {"status": "not_checked", "evidence": "Lighthouse not available in this session"}
  }
}
```

Rules `score.py report` enforces:
- every dimension present and 1–10 for every site
- every catalogue check recorded (use `not_checked` rather than leaving one out)
- `fail` and `partial` need evidence
- no check IDs outside the catalogue

## 6. Baseline and targets (2026-10-09)

| Dimension | Forward Deployed | Target | Best competitor |
| --- | --- | --- | --- |
| coverage | 7 | 8 | Aced 8 |
| depth | 9 | 9 | Hello Interview, ByteByteGo 8 |
| practice | 7 | 8 | Hello Interview, Aced 8 |
| grounding | 4 | 7 | Aced 9 |
| credibility | 3 | 8 | several at 9 |
| navigation | 3 | 8 | Hello Interview, Tech Interview Handbook 9 |
| onboarding | 4 | 8 | Hello Interview, Tech Interview Handbook 9 |
| template | 5 | 8 | Hello Interview, Tech Interview Handbook 9 |
| progress | 6 | 8 | roadmap.sh 9 |
| polish | 4 | 9 | most at 9 |

Baseline: content 6.0 (3rd of 7), structure 4.4 (7th of 7), overall 5.2 (7th of 7). Target after the 12-week plan: content 8.0, structure 8.2, overall 8.1.
