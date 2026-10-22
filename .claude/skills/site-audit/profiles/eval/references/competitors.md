# Competitor benchmark

Agent Evaluation Demystified is compared with the places an engineer actually goes to learn LLM and agent evaluation: practitioner writing, vendor guides and docs, and short courses. First benchmarked 2026-10-14 (scores below). Re-benchmark when the last benchmark is more than 90 days old, when the owner asks, or when a competitor launches something material (a course, an interactive tool, a new guide). Otherwise carry their scores forward with their `scores_as_of` date: re-scoring without re-reading makes the comparison drift.

## Sites and what to open

All URLs returned 200 on 2026-10-14. Swap any that move. OpenAI's moved on 2026-10-14 (301/308) and are listed at their new home.

| Key | Site | Pages to open | Why it is a comparable |
| --- | --- | --- | --- |
| `hamel-evals` | Hamel Husain | https://hamel.dev/blog/posts/evals/, https://hamel.dev/blog/posts/evals-faq/ | The most-cited practitioner writing on evals: error analysis, judges validated against humans, an FAQ format |
| `eugene-yan` | Eugene Yan | https://eugeneyan.com/writing/evals/ | Task-specific metric guidance with what works and what does not; dense, one-page format |
| `evidently-guide` | Evidently AI LLM guide | https://www.evidentlyai.com/llm-guide, https://www.evidentlyai.com/llm-guide/llm-evaluation | Vendor-written but tool-agnostic multi-chapter guide; closest structural match (a guided curriculum site) |
| `deepeval-docs` | DeepEval docs and guides | https://deepeval.com/docs/getting-started, https://deepeval.com/guides/guides-rag-evaluation | The framework this repo uses most; metric reference plus RAG and agent guides |
| `openai-evals-guide` | OpenAI evaluation guides | https://developers.openai.com/api/docs/guides/evaluation-best-practices, https://developers.openai.com/cookbook | The guide this site audits itself against (OpenAI guide audit page) |
| `deeplearning-ai` | DeepLearning.AI short courses | https://www.deeplearning.ai/short-courses/evaluating-ai-agents/, https://www.deeplearning.ai/short-courses/ | Hands-on video courses with notebooks, including the Arize agent-evaluation course this repo carries under `labs/` |

Not scored: Arize Phoenix docs (`arize.com/docs/phoenix` refused scripted fetches with 403; open in the browser if you want to add it), RAGAS docs (reference documentation, not a learning path).

Also search for new evaluation learning sites each time (queries: `LLM evaluation course`, `agent evaluation guide`, `RAG evaluation tutorial`). Add a site only when it is a learning resource with more than one page on evaluation.

## Scores (2026-10-14)

| Site | coverage | depth | practice | grounding | credibility | navigation | onboarding | template | progress | polish | Content | Structure | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepEval docs | 7 | 5 | 3 | 9 | 7 | 9 | 8 | 8 | 6 | 9 | 6.2 | 8.0 | 7.1 |
| DeepLearning.AI | 5 | 5 | 7 | 7 | 8 | 7 | 6 | 8 | 7 | 9 | 6.4 | 7.4 | 6.9 |
| Hamel Husain | 7 | 9 | 2 | 3 | 9 | 4 | 5 | 7 | 4 | 8 | 6.0 | 5.6 | 5.8 |
| OpenAI guides | 6 | 6 | 2 | 4 | 5 | 7 | 4 | 7 | 5 | 9 | 4.6 | 6.4 | 5.5 |
| **Agent Evaluation Demystified** | 8 | 8 | 7 | 4 | 4 | 5 | 4 | 6 | 5 | 3 | 6.2 | 4.6 | 5.4 |
| Eugene Yan | 3 | 8 | 2 | 5 | 9 | 4 | 3 | 7 | 4 | 8 | 5.4 | 5.2 | 5.3 |
| Evidently AI | 6 | 4 | 2 | 2 | 5 | 6 | 5 | 5 | 2 | 7 | 3.8 | 5.0 | 4.4 |

Notes from 2026-10-14: none of the six has an open interactive tool or hidden-answer drill (DeepLearning.AI's graded quiz is the only checked practice); only DeepEval states a library version (v4.2.8 selector); OpenAI's Evals platform goes read-only 31 Oct 2026 and shuts 30 Nov 2026; Hamel's FAQ (Husain and Shankar, Sep 2026) has five reading paths; Evidently's article has an unpopulated contents template. Hamel's FAQ was read to ~100k of 152k characters.

## Patterns strong learning sites share (what to keep checking against)

1. A stated audience and one first step ("start here"), with a short path for people in a hurry.
2. Concepts tied to runnable code or a notebook on the same page.
3. Worked examples with real numbers, and what each metric misses.
4. Named author, dates, and a way to report errors on every page.
5. Search across all pages.
6. Content in one consistent template; interactive pieces that look like part of the site.
7. Practice that hides the answer until the reader commits.

## Re-benchmark procedure

1. Run the competitor prompt in `<profile>/references/agent-prompts.md` with the URLs above.
2. Open the pages yourself for any site whose score would change by 2+ on a dimension.
3. Add or update `scores.<key>` and `scores_as_of.<key>` in `scores.json`; explain each change in `notes`.
4. Record the scores in a table here (dimensions, Content, Structure, Overall) with the date, and update the notes column if a site changed materially.
