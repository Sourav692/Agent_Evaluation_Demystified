# Competitor benchmark

Six sites were benchmarked on 2026-10-09. Re-benchmark them when the last benchmark is more than 90 days old, when the owner asks, or when a competitor launches something FDE-specific. Otherwise carry their scores forward with their `scores_as_of` date — re-scoring competitors without re-reading them makes the comparison drift.

## Sites and what to open

| Key | Site | Pages to open | Notes from 2026-10-09 |
| --- | --- | --- | --- |
| `hello-interview` | Hello Interview | https://www.hellointerview.com/learn, https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction, https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly | 2 content nav items + search; "In a Hurry" express track; fixed worked-answer template ending "What is expected at each level"; author and updated date on pages; Mark as read; Vote for new content; ML system design and AI Coding tracks; company question pages incl. OpenAI and Anthropic; no FDE content seen |
| `aced` | Aced (formerly Exponent) | https://www.aced.io/, https://www.aced.io/guides/databricks-forward-deployed-engineer-interview, https://www.tryexponent.com/blog/forward-deployed-engineer-interview-the-definitive-2026-guide-fde | tryexponent.com redirects to aced.io. Forward Deployed Engineering course (Beta) aimed at Anthropic, OpenAI, Palantir loops; behavioural lessons with sample answers and analyses; guides one section per round, "Updated X days ago by candidates", Suggest edits; question bank filters by role, company, type. Lesson pages render client-side and could not be read |
| `bytebytego` | ByteByteGo | https://bytebytego.com, https://bytebytego.com/courses/genai-system-design-interview | 8 course cards, no top nav; GenAI System Design course has 11 chapters (Smart Compose, Translate, ChatGPT, RAG, image/video generation); chapter sidebar with "0/31 completed"; bestselling authors, 5M+ audience |
| `tech-interview-handbook` | Tech Interview Handbook | https://www.techinterviewhandbook.org, https://www.techinterviewhandbook.org/system-design/ | 6 nav items; four numbered stages on home; Docusaurus template with sidebar, breadcrumbs, contents, prev/next, last updated; named author, 142k GitHub stars; no AI or FDE content |
| `roadmap-sh` | roadmap.sh | https://roadmap.sh, https://roadmap.sh/roadmaps, https://roadmap.sh/ai-engineer | 4 nav items + search; role vs skill roadmaps with filter chips and counts; "Coming soon" only on items; dated public changelog; AI Engineer roadmap is links-based |
| `deeplearning-ai` | DeepLearning.AI short courses | https://www.deeplearning.ai/short-courses/, https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/ | 5 nav items; filters by type, level, topic with counts; course header with level, duration, updated date, instructors; hands-on agent/RAG courses, not interview prep |

Not scored: NeetCode (client-rendered, not readable by fetch tools).

Also search for new FDE-specific prep sites each time (query: `forward deployed engineer interview prep`). In October 2026 the direct FDE competition was Aced's FDE course and guide, a product-pitch guide from Perspective AI, and the paid FDE Academy cohort; none had a worked AI casebook.

## Baseline scores (2026-10-09)

| Site | coverage | depth | practice | grounding | credibility | navigation | onboarding | template | progress | polish | Content | Structure | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hello Interview | 6 | 8 | 8 | 8 | 9 | 9 | 9 | 9 | 8 | 9 | 7.8 | 8.8 | 8.3 |
| Aced | 8 | 6 | 8 | 9 | 8 | 7 | 7 | 7 | 8 | 9 | 7.8 | 7.6 | 7.7 |
| Tech Interview Handbook | 3 | 6 | 4 | 5 | 9 | 9 | 9 | 9 | 6 | 9 | 5.4 | 8.4 | 6.9 |
| DeepLearning.AI | 5 | 7 | 6 | 2 | 9 | 8 | 7 | 8 | 8 | 9 | 5.8 | 8.0 | 6.9 |
| ByteByteGo | 5 | 8 | 3 | 4 | 9 | 8 | 7 | 8 | 6 | 9 | 5.8 | 7.6 | 6.7 |
| roadmap.sh | 4 | 3 | 5 | 2 | 8 | 8 | 7 | 8 | 9 | 9 | 4.4 | 8.2 | 6.3 |
| Forward Deployed | 7 | 9 | 7 | 4 | 3 | 3 | 4 | 5 | 6 | 4 | 6.0 | 4.4 | 5.2 |

Limits: paid lesson pages on Aced and ByteByteGo were not readable, so their depth scores rest on outlines. General-purpose sites score low on FDE coverage by design; they are included because FDE candidates use them alongside FDE-specific material.

## Patterns strong prep sites share (what to keep checking against)

1. 4–6 top-nav items; extras in the footer or a More menu.
2. One dominant first step, worded as an action; an express lane in front of the full curriculum.
3. Content sliced at least two ways (topic plus stage, role or company).
4. Worked solutions follow one fixed template ending in level calibration.
5. Try first, then see the answer.
6. Simple visible progress (a counter or Mark as read).
7. Freshness and author on every content page.
8. Unfinished content labelled as small items, never as whole nav areas; a way to vote for what comes next.
9. Filter chips with counts on list pages, plus ⌘K search.

## Re-benchmark procedure

1. Run the competitor prompt in `<profile>/references/agent-prompts.md` with the URLs above (swap any that moved).
2. Open the pages yourself for any site whose score would change by 2+ on a dimension.
3. Update `scores.<key>` and `scores_as_of.<key>` in `scores.json`; explain each change in `notes`.
4. Update the notes column in this file if a site changed materially (new FDE material, redesign).
