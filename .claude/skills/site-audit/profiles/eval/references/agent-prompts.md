# Subagent prompts

A full audit reads most of the site's ~30 pages through three parallel reading tracks, plus a competitor benchmark when one is due. Launch the tracks in one message so they run together (Agent tool, `general-purpose`). Placeholders:

- `{BASE}` — site root (`https://eval-demystified.vercel.app`)
- `{URLS}` — the pages for that track. Build the list from this audit's `inventory.json` (`pages[].path` and `kind`); the lists below are the starting point and use today's slugs.
- `{CHECKS}` — the IDs and titles of the checks that track covers, copied from `<profile>/data/checks.json`

Two page families exist (see SKILL.md): **rendered** pages (from Markdown, served text is complete) and **copied** standalone HTML (labs, drill, study plan, tutorial, playbook, stratified reporting). The drill and the labs draw most of their content with JavaScript, so WebFetch sees little of them — those belong to the browser checks, not the tracks.

Ask every track for findings mapped to check IDs. That keeps their output directly usable in `scores.json`.

## Shared output contract (append to every prompt)

```
Report strictly what the pages contain; never guess. WebFetch reads served text,
so anything drawn by JavaScript (diagrams, quiz state, lab numbers) may be missing:
say "not visible in fetched text" rather than calling it absent.

End with a section "Check results" containing one line per check ID you assessed:
<ID> | pass / partial / fail / not_checked | evidence (URL + short quote or count)
Then "New issues" for problems that fit no listed check, each with URL evidence.
Keep the whole report under 1,400 words.
```

## Track A — onboarding, start pages and trust

Checks: ON-01 to ON-06, FV-04, FV-06, PR-05, PR-14, PR-15.

URLs: `/index.html`, `/roadmap.html`, `/evaluation-study-plan.html`, `/00-orientation.html`, `/question-bank.html` (first screen and appendices only), `/fde-playbook-audit.html`, `/openai-audit.html`.

```
You are auditing {BASE}, a free learning site for engineers who must evaluate RAG
systems and AI agents, or answer for that in an eval-heavy interview round. Focus:
onboarding and trust. Use WebFetch on every URL below.

URLs: {URLS}

For each page report: H1 and purpose; sections in order; calls to action and where
they go; time estimates; who the page says it is for; rough length; and problems:
dead ends, duplicated purpose with another page, naming that differs between pages,
build or repository internals shown to readers.

Then answer, with URL evidence:
1. What does a first-time visitor see first on the index: audience, promise, one
   first step? Quote it.
2. The index, the roadmap, the study plan and Level 0 each suggest where to start.
   Do they agree on order and time? Do they link to each other?
3. Is there a lane for someone interviewing this week (fast path, drill)? Is it
   visible from the index?
4. Does any page say who maintains the site, their background, how to reach them,
   or when it was last updated?
5. Which pages are built on third-party material (OpenAI's evaluation guide, an FDE
   playbook, DeepLearning.AI x Arize course material)? Is the source credited and is
   the permission to reuse it stated?
6. List every count the index and these pages claim (questions, cases, levels, labs,
   stages, gotchas, TODOs) so it can be checked against FV-04.

Checks to assess: {CHECKS}
<shared output contract>
```

## Track B — structure, overlap and cross-links

Checks: IA-04, IA-06, IA-07, CT-01, CT-11.

URLs: `/index.html`, `/question-bank.html`, `/roadmap.html`, `/field-guide.html`, `/01-rag-retrieval-and-generation.html`, `/02-agents-tools-conversations-trajectories-outcomes.html`, `/openai-audit.html`, `/openai-eval-guide-tutorial.html`, `/fde-playbook-audit.html`, `/fde-playbook-end-to-end-evaluation.html`, `/online-vs-offline.html`, `/07-online-evaluation-and-the-loop.html`, `/databricks-mlflow.html`, `/stratified-reporting-explained.html`, `/05-statistics-and-stratified-reporting.html`.

```
You are auditing {BASE}, a learning site on evaluating RAG systems and AI agents.
Focus: how content is split between pages, and whether overlapping pages say why
both exist. Use WebFetch on every URL below.

URLs: {URLS}

For each page report: H1 and purpose; main sections; which other pages on the site
it links to; the lab, drill section or notebook it points the reader to.

Then answer, with URL evidence:
1. These pairs overlap: question bank and drill; roadmap and the Level 0-10
   explainers; OpenAI guide audit and the tutorial; field guide and Levels 1-2;
   FDE playbook audit and the end-to-end evaluation page; stratified reporting
   page and Level 5; online-vs-offline and Level 7. For each pair: is the overlap
   declared (what each is for), and do they link each other both ways?
2. Does each theory page and explainer link to the lab, drill section or notebook
   that practises it? Does each lab link back to its theory?
3. For each of these surfaces, name the page that treats it substantively, or say
   none does: retrieval, generation, tool use, trajectory, multi-turn, LLM judges,
   human labels, statistics, release gate/CI, online evaluation, safety, cost and
   guardrails, ownership and sign-off.
4. Do index card titles, page titles and H1s use the same words? List mismatches.

Checks to assess: {CHECKS}
<shared output contract>
```

## Track C — page quality, depth and grounding

Checks: PQ-05, PQ-07, PQ-10, CT-03, CT-04, CT-07, CT-08, CT-10.

URLs: all eleven explainers (`/00-orientation.html` … `/10-the-enterprise-harness-end-to-end.html`), plus `/field-guide.html`, `/databricks-mlflow.html`, `/online-vs-offline.html`. Add any page the scan flagged under PQ-06, PQ-07 or CT-10.

```
You are auditing the teaching pages of {BASE}, a learning site on evaluating RAG
systems and AI agents, for depth, consistency and how well the prose is tied to
runnable code. Use WebFetch on every URL below.

URLs: {URLS}

For each page report: H1; section headings (are they imperative, e.g. "Pin Six
Expectations, Not One"?); whether it has a worked example with concrete numbers
(quote one number); Key Takeaways; Check Yourself (are answers hidden?);
References; links to notebooks (github.com/.../courses/...ipynb) or labs; code
blocks and which library they use; author or last-updated line; and problems:
copy errors, claims that contradict the list beneath them, library APIs that look
retired.

Library versions the repo pins: deepeval 4.2.3 (GEval takes SingleTurnParams, not
LLMTestCaseParams), ragas 0.4.3 (metrics in ragas.metrics.collections with async
ascore()), MLflow 3 GenAI (mlflow.genai.evaluate and scorers). Flag any code that
shows an older API as current; an older API named only to warn against it is fine.

Then summarise: (a) which explainers deviate from the shared format and how;
(b) which pages lack a worked example with numbers; (c) for each metric family,
whether the site says what it misses or how it can mislead; (d) which of DeepEval,
RAGAS, MLflow and Phoenix appear in code, and where.

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

When a benchmark is due (see `<profile>/references/competitors.md`). Fill the placeholders:

- `{COMPETITOR_URLS}` — the "Pages to open" column of `<profile>/references/competitors.md`, one site per line
- `{LAST_DATE}` — the `scores_as_of` date being replaced, or "never" on the first benchmark
- `{RUBRIC_SUMMARY}` — the ten one-line dimension definitions from `<profile>/references/rubric.md` §2–3 (the sentence under each heading)

```
I'm benchmarking a learning site on evaluating RAG systems and AI agents ({BASE})
against comparable resources. For each site below, fetch the pages listed (skip any
that block fetching and say so). Report concisely: who it is for; how content is
grouped; how a newcomer is told where to start; how concepts are tied to code or
notebooks; worked examples and failure modes; practice (quizzes, exercises,
interactive tools); content-page features (contents, prev/next, reading time,
last updated, author); search; trust signals; and anything new since {LAST_DATE}.

Sites: {COMPETITOR_URLS}

Then, for each site, propose a 1-10 score on these ten dimensions with one line of
evidence each: coverage, depth, practice, grounding, credibility, navigation,
onboarding, template, progress, polish (definitions: {RUBRIC_SUMMARY}).
A single blog post scores low on navigation and onboarding by design; say so rather
than inflating. Strictly factual; cite URLs. Under 1,500 words.
```
