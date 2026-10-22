# Subagent prompts

The first audit read about 50 pages through three parallel reading tracks plus a competitor benchmark. Launch the tracks in one message so they run together (Agent tool, `general-purpose`). Each prompt below has placeholders:

- `{BASE}` — site root
- `{URLS}` — the pages for that track. Build the list from this audit's `inventory.json` (the structure may have changed since the baseline). The baseline lists are given as a starting point; swap each for its current equivalent and add any new hubs.
- `{CHECKS}` — the IDs and titles of the checks that track covers, copied from `<profile>/data/checks.json`

Ask every track for findings mapped to check IDs. That keeps their output directly usable in `scores.json` and stops vague prose.

## Shared output contract (append to every prompt)

```
Report strictly what the pages contain; never guess. WebFetch reads served text,
so anything drawn by JavaScript (badges, diagrams, saved progress) may be missing:
say "not visible in fetched text" rather than calling it absent.

End with a section "Check results" containing one line per check ID you assessed:
<ID> | pass / partial / fail / not_checked | evidence (URL + short quote or count)
Then "New issues" for problems that fit no listed check, each with URL evidence.
Keep the whole report under 1,400 words.
```

## Track A — onboarding, hubs and utility pages

Checks: ON-01 to ON-08, IA-07, IA-08, IA-12, FV-04, PR-05, PR-14, PR-15.

Baseline URLs: `/start`, `/start/paths/beginner`, `/start/paths/fde`, `/start/paths/revision`, `/start/paths/fde-frontier-lab`, `/learning-map`, `/guide`, `/learn/orientation`, `/learn/orientation/how-the-platform-works`, `/learn/orientation/how-the-platform-works/choose-a-reading-path`, `/glossary`, `/library`, `/library/credits`, plus `/about` and `/changelog` if they exist.

```
You are auditing {BASE}, a learning and interview-prep site for Forward Deployed
Engineer (FDE) candidates, for onboarding clarity and trust. Use WebFetch on every
URL below.

URLs: {URLS}

For each page report: H1 and purpose; sections in order; navigation aids
(breadcrumbs, sidebar, contents, prev/next, progress); primary calls to action and
where they go; status labels shown; rough length; and problems: placeholders,
dead ends, duplicated purpose with another page, naming that differs between
pages, internal numbering or file names visible to users, unclear calls to action.

Then answer: How many pages explain how to use the site or which path to take,
and do they agree (paths, hours, counts)? Does any path mark an unready module as
required? Is there an About/author page, and what does Credits say about where
material comes from? Are all paths, including loop variants, visible on the start
page with hours?

Checks to assess: {CHECKS}
<shared output contract>
```

## Track B — section hubs and how content is split

Checks: IA-01 to IA-06, IA-09, IA-10, IA-13, FV-02, FV-03, PQ-11, CT-02, CT-03, CT-04, CT-06, CT-07, CT-10.

Baseline URLs: `/learn`, `/design`, `/practice`, `/interview`, `/interview/case-study-worksheets`, `/interview/mock-interviews`, `/interview/final-week`, `/interview/company-loops`, `/interview/coding-round-practice`, `/company-prep`, `/fde-last-day-prep`, `/fde-last-day-prep/roadmap`, `/fde-last-day-prep/rapid-revision`, `/modules/15-fde-case-studies`, `/modules/01-customer-discovery-and-decomposition`, `/modules/14-behavioural-and-leadership-round`, `/learn/ai-systems-design/classic-ai-designs`, `/learn/ai-systems-design/scenario-library`.

```
You are auditing {BASE}, a learning and interview-prep site for FDE candidates.
Focus: the section hubs and how content is split between them. Use WebFetch on
every URL below.

URLs: {URLS}

For each page report: H1 and purpose; sections in order; how items are listed and
whether there are filters, search, tags, difficulty, time estimates or status
badges; counts of items; calls to action; navigation aids; problems.

Then answer, with URL evidence:
1. Does any set of content (worked designs, worksheets, final-week reviews, mocks)
   have more than one index page? List each set and every page that indexes it.
2. Fetch one worksheet and its case-study twin (same scenario in two places). Are
   they duplicates, different depths, merged, or cross-linked both ways?
3. Is the boundary between the design, practice and interview/final-week areas
   clear? Does any top-nav destination have no real content?
4. Do the counts on hubs match the homepage claims {HOME_COUNTS}?
5. How many URL schemes exist, and do breadcrumbs and back links point to the hub
   in the top nav?
6. Is there material for company loops, the coding round, client simulation or a
   take-home, reported questions, and video or spoken practice?

Checks to assess: {CHECKS}
<shared output contract>
```

`{HOME_COUNTS}` comes from `scan-checks.json` → `FV-04` details.

## Track C — page template and content quality

Checks: PQ-02 to PQ-06, PQ-08, PQ-09, PQ-10, PQ-15, FV-05, CT-01, CT-08, CT-09.

Baseline URLs (one or two per page type): `/learn/llm-and-retrieval`, `/learn/llm-and-retrieval/rag-from-first-principles`, `/learn/llm-and-retrieval/rag-from-first-principles/the-rag-pipeline-end-to-end`, `/learn/llm-and-retrieval/ml-fundamentals`, `/learn/engineering-foundations/python-for-ai-services`, `/learn/agentic-systems/the-tool-calling-loop/the-tool-calling-loop-from-scratch`, `/learn/production-ai/agentops/agentops-mapped-to-databricks`, `/learn/forward-deployed/judgement-cases`, `/learn/capstone-and-portfolio/portfolio-write-up`, `/modules/01-customer-discovery-and-decomposition/core/internal-knowledge-assistant`, `/modules/15-fde-case-studies/knowledge-retrieval/enterprise-knowledge-assistant`, `/modules/15-fde-case-studies/judgement-and-decomposition/decomposition-classics-67-68-69`, `/modules/14-behavioural-and-leadership-round/story-bank`, `/interview/mock-interviews/internal-knowledge-assistant-mock-interview`, two final-week review pages and the cheat sheet.

Add any page the scan flagged under PQ-07, PQ-08, PQ-09 or PQ-12 that is not already listed.

```
You are auditing the content pages of {BASE}, a learning and interview-prep site for
FDE candidates, for page-template consistency, readability and production
readiness. Use WebFetch on every URL below.

URLs: {URLS}

For each page report: page type; H1; whether it shares the main site header, nav
and footer; breadcrumbs; on-page contents; prev/next links; reading time and level
(note if two different reading times appear); status badge; learning objectives
(quote the label used); key takeaways; diagrams; code blocks; practice prompts;
last-updated date; author; length; and problems: placeholder text, stubs, internal
numbering or file names in titles or text, inconsistent heading style or spelling,
claims that contradict the list beneath them.

Then summarise: (a) how many distinct page layouts exist and how they differ;
(b) which pages are stubs; (c) titles or URLs that look like internal file names;
(d) whether worked designs end with what Senior / Staff answers cover.

Checks to assess: {CHECKS}
<shared output contract>
```

## Verifier — before the report

Run after the tracks return, on the fails that are surprising, decisive for a score, or contradict the previous audit. Prefer doing this yourself in the browser (`<profile>/references/browser-checks.md`); use this prompt when no browser is available.

```
Independently verify these audit findings on {BASE}. For each, fetch the URL and
state CONFIRMED, NOT CONFIRMED or CANNOT TELL (e.g. content drawn by JavaScript),
with the quote or count you saw. Do not trust the claim; look for yourself.

Findings:
{FINDINGS — one per line: check ID | claim | URL}
```

## Competitor benchmark

Only when re-benchmarking (see `<profile>/references/competitors.md`). Fill the placeholders:

- `{COMPETITOR_URLS}` — the "Pages to open" column of `<profile>/references/competitors.md`, one site per line
- `{LAST_DATE}` — the `scores_as_of` date of the competitor scores being replaced
- `{RUBRIC_SUMMARY}` — the ten one-line dimension definitions from `<profile>/references/rubric.md` §2–3 (the sentence under each heading)

```
I'm re-benchmarking an FDE interview-prep site ({BASE}) against comparable sites.
For each site below, fetch the home page and one representative content page
(skip any that block fetching and say so). Report concisely: top-nav labels and
count; how content is grouped (role, topic, stage, company); how a newcomer is
onboarded; content-page features (sidebar, breadcrumbs, prev/next, reading time,
difficulty, progress, last updated, author); how unfinished content is shown; trust
signals; filters and search on list pages; and anything new since {LAST_DATE}
relevant to FDE candidates (FDE courses, company guides, AI system design).

Sites: {COMPETITOR_URLS}

Then, for each site, propose a 1–10 score on these ten dimensions with one line of
evidence each: coverage, depth, practice, grounding, credibility, navigation,
onboarding, template, progress, polish (definitions: {RUBRIC_SUMMARY}).
Strictly factual; cite URLs. Under 1,500 words.
```
