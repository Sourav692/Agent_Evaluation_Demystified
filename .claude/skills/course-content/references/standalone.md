> **Required:** Apply `references/source-fidelity.md` first. Preserve all source concepts and diagrams. Rename non-contract headings when clearer, and verify the source-to-output coverage matrix before export.

# Standalone mode

A lesson page for forwarddeployedprep.com that is **not** a course theory page: a topic outside the 46 modules, or another track (AI Engineering, Data Engineering, Agentic Engineering, AI System Design). Output is two files, Markdown plus a self-contained HTML page in the Forward Deployed house style, built by `standalone/scripts/build_site.py`. Produce one format only when the user asks for one.

`CLAUDE.md` forbids per-lesson HTML inside part folders, so these files go to `<track-slug>/<NN>-<topic-slug>.md` at the repo root (e.g. `agentic-engineering/01-agentic-patterns-from-scratch.md`; these folders are untracked), or to the folder the user names. Never write them into a theory folder. A course module's theory always uses create or rewrite mode instead.

`lesson.md` and `voice.md` apply in full, including theory only: no code blocks, no `#### OUTPUT ####` blocks. `standalone/references/example-lesson.md` and its approved `.html` are the current target. Use approved-format.md and components.md for the frame and optional interactions. For a course lesson, use the repository workflow and `scripts/export_lesson.py`. If the user requests only a standalone HTML review, preserve the source README and produce the requested artifact. Still update its module row in `REWRITE_TRACKER.md` under the required rewrite-tracking rule in `SKILL.md`.

## Workflow

1. **Pin the brief**: track, topic, template (concept lesson or system design), level (default intermediate), previous and next lesson. Ask one question only if the topic or template is unclear; otherwise state the choice at the top of the reply.
2. **Check facts that move** (APIs, model names, prices, benchmarks, product features) with Context7 or web search. Keep the sources; they become References. Never invent a citation, number or signature.
3. **Outline**: heading skeleton, one line per section with what it teaches and which diagram goes there.
4. **Draft**, then the `voice.md` quality gate and `no-ai-slop`.
5. **Build**:
   ```bash
   python3 .claude/skills/course-content/standalone/scripts/build_site.py <track-slug>/<NN>-<topic-slug>.md
   ```
   Needs `markdown` and `pyyaml`; the first run installs mermaid-cli and fonts into `~/.cache/content-write` (npm and Chrome). A failing Mermaid block is printed: fix it and rerun.
6. **Check** in headless Chrome: 1254px and 390px (no sideways scroll), light and dark (`document.documentElement.dataset.theme='dark'`). Look at every diagram.
7. Send both paths.

## Frontmatter

```yaml
---
title: "<Plain, descriptive title in sentence case>"
subtitle: <one line naming what the page resolves>
track: <AI Engineering | Data Engineering | Agentic Engineering | AI System Design>
module_group: <e.g. Agent Foundations>
module_code: <e.g. T7.1>
module_name: <e.g. The Agent Loop & Tool Calling>
lesson: <N>
lessons: ["<lesson 1 title>", "<lesson 2 title>"]   # every lesson in the module, in order (sidebar)
level: <beginner | intermediate | advanced>
reading_time: <N> min
source: <display label, e.g. From the RAG & Agents Engineering course>
source_url: <original lesson URL when adapting a published source>
author: Sourav Banerjee
last_updated: <optional; replaces Level in the meta row>
prerequisites: [<lesson slugs>]
tags: [<3 to 6 tags>]
---
```

Title and every heading in sentence case.

## Concept lesson (default)

Use the approved example's problem-first teaching sequence. Adapt non-contract section titles and ordering to the source. Retain source checks, notebook destinations and navigation. Do not force an unrelated recap or next-lesson link when none was supplied.

## System design case study coverage (new cases without a source)

For a new unsourced case, cover these areas in suitable descriptive sections. A source-derived case preserves its material and adapts the approved teaching pattern. Areas: Clarifying requirements (functional and non-functional lists, scale table); Framing the problem (input, output, task type, chosen approach and why alternatives lose); Data (sources, volume, labelling, pipeline diagram); Model or core logic (architecture diagram, strategy, key formula with a worked number); Evaluation (offline and online metrics tables tied to business goals); Overall system design (end-to-end diagram, one or two sentences per component); Deployment, scaling and monitoring (serving path, latency and cost math, alerts); Summary; References. Talking points (4 to 8 bold-label questions) after each of the model, evaluation, system and deployment sections. Show one back-of-envelope estimate (QPS, storage, tokens, cost or GPU-hours) with its arithmetic.

## Diagrams

Mermaid wherever a concept has flow, architecture, interaction over time, states, a decision, a data model or phases; as many as source coverage and explanation require. Preserve all source diagrams, including paired architecture figures; do not remove one to fit a numeric target. Place each right after the claim it supports, then a caption `*Figure N: ...*` (tables: `*Table N: ...*`) and refer to it by number. At most 12 nodes, labels of 4 words or fewer, one idea per diagram, short alphanumeric node ids, quoted labels with punctuation, edges labelled with the verb or data that moves, `subgraph` for boundaries, no colours unless they encode meaning. The site theme comes from `standalone/assets/mermaid-*.json`; restyle there, not per diagram.

## Track emphasis

- **AI Engineering**: the model-call boundary (prompts, context, retrieval, evaluation, latency, cost per request). Include a token or cost estimate and an evaluation section.
- **Data Engineering**: data flow and guarantees (batch vs streaming, partitioning, file sizes, idempotency, schema evolution, SLAs). Include a pipeline diagram and a sizing estimate.
- **Agentic Engineering**: control flow and failure (the loop, tool contracts, state, guardrails, human in the loop, observability, evals). Include a `sequenceDiagram` or `stateDiagram-v2` of the loop and named failure modes.
- **AI System Design**: cover the system-design areas above for a new case; preserve source-derived case material when adapting an existing lesson.

Explain vendor-neutrally first; name a product only as one implementation.

## House style

Fixed in `standalone/assets/site.css` and the Mermaid theme files; edit those, never the generated HTML. Bricolage Grotesque display and Inter body; paper `#f7f5f0` / `#161513`; one green accent `#007439` / `#3fae73`; warnings `#9a5b00` / `#e0a24a`; callouts are fill plus a 3px accent edge, no emoji. Mermaid themes must set `stateLabelColor` and actor, signal and note text colours, or labels vanish in state diagrams.
