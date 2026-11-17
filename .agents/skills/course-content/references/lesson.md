# Lesson construction

Use approved-format.md for presentation and editorial-explainer.md for teaching. The approved example is the current target. Its section names and six-stage process belong to its subject; they are not mandatory headings or counts for another lesson. Source fidelity and real repository contracts govern what must remain.

## A learning sequence that fits the source

Open on a concrete user need or failure. Explain the mechanism in plain language, then show its architecture and follow the same input through decisions, state changes and output. When there are genuine alternatives, explain and diagram each independently before the shared comparison. Close the relevant discussion with an actionable choice, its failure modes and its evidence limits.

Reorder or rename non-contract sections to improve that learning sequence. Do not force separate Recap, The problem, Summary, Talking points or Next headings into a source adaptation. Add a short prerequisite bridge or real next-lesson destination when it helps and exists. Keep a source's notebook section and checks in their required repository slots or their retained standalone positions.

A useful page covers these outcomes, in natural sections rather than a repeated template:

| Reader outcome | Material that can teach it |
| --- | --- |
| Recognise the failure | One concrete question, near miss or incident |
| Explain the mechanism | A definition, architecture diagram and component roles |
| Trace what changes | Input, decision, state and output through one example |
| Compare genuine alternatives | Separate explanations and diagrams, then shared input/results and a decision table |
| Diagnose a failure | A bad case, observed consequence and a guard tied to that mechanism |
| Choose in practice | Cost, latency, recovery or operational consequences supported by the source |
| Respect the evidence | Provenance, exact results, uncertainty, negative findings and limits |
| Check understanding | Concise takeaways and conceptual questions answered by the lesson |

Use the source's scenario, terminology and numbers. Illustrative additions are labelled. A process may earn a walkthrough; a meaningful choice may earn a switcher. A static figure may be enough. The component must expose a mechanism, not consume space.

## Implementation becomes evidence

Keep executable code in notebooks. Translate a function into its responsibility and position in the architecture. Translate code/output into a traced table or result with provenance. Translate raw protocol/JSON into a field table when the fields teach the mechanism. Translate a notebook-only exercise into a conceptual self-check. Mermaid is the only allowed fenced block.

## Figures, tables and limits

Preserve every inventoried source diagram, including distinct diagrams from supplied adaptations. A comparison of architectures keeps a separate labelled diagram for each approach. A switcher supplements those diagrams. Do not remove a figure to fit a numeric cap.

Introduce each figure or table with the claim it explains. Give it a sequential numbered caption, then explain what follows from the evidence. Keep the original source figures in their relative order. New figures use short labels and one main idea. A source figure that is wider than a phone scrolls locally instead of shrinking its labels beyond readability. Record protected image hashes and required figure IDs in the manifest.

Default full prose budget is 2,500 words, including every static interaction panel. Trim repeated explanations and optional additions before source concepts. An explicitly authorised higher limit is recorded in the manifest; a live site's own required checks still apply. Do not invent performance numbers to fill a cost table. Use an estimate only when its inputs and arithmetic are stated.

## Repository contracts

For a course README, keep its required title/header line, exact curriculum concept headings, importer/diagram/lab markers, previous/next destinations and Key Takeaways/Check yourself conventions. `contracts.md` describes those hooks. The generated notebook slot remains generated.

For a standalone source adaptation, use the approved shell and preserve source checks and notebook destinations. Retain three source self-checks when supplied; do not replace them with a fixed new question template. For a new lesson, choose mechanism, application and diagnosis questions that the page answers.

A project page is appropriate for a notebook that demonstrates an application without a new concept of its own. The reference below applies when that actual course case occurs; it does not replace a source-derived concept lesson.

## Project page

A lesson whose notebook builds something (an app, a bot, a pipeline on live data) and teaches no concept of its own gets a short project page instead of a *planned* row. 600 to 1,200 words, same header line, subtitle, Key Takeaways, Check yourself and footer, no code. In order:

1. **`## The project: <name>`**, opening with a `> **What you'll build**` callout (3 to 5 bullets), then two short paragraphs: what the project does with which earlier lesson's pattern, and what changes when the pattern leaves the notebook.
2. **`## Architecture`**: one Mermaid figure of the pieces and a table *Piece · What it does · Built on* (the earlier lesson each piece reuses).
3. **`## Following <one request>`**: one request traced through the pieces (a sequence figure or table). Live data: describe the call order, never quote values a rerun would change.
4. **`## Design choices worth copying`**: a table *Choice · Why*, linking each to the lesson that names its risk.
5. **`## Limits`**: what the build leaves out or gets wrong, and one sentence on what it needs to run (keys, optional dependency groups), without commands.

Example: M22 lesson 22.2 (`optional/theory/02_a_real_world_agent_on_raw_api_calls_hacker_news_chatbot/`).

## Notebook links

For course pages, notebooks appear only in the header line. A standalone source adaptation may retain its existing notebook section when no importer generates it; see source-fidelity.md. The site importer (`site/scripts/rag-theory-import.mjs` in the site repo) and `export_lesson.py` turn that line into a **Run the notebooks** section before Key Takeaways, with an *Open on GitHub* and an *Open in Colab* link per notebook. Never write that section by hand.
