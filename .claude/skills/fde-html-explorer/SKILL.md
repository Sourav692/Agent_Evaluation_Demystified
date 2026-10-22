---
name: fde-html-explorer
description: Create a standalone HTML explorer for any FDE system-design or architecture interview use case. Use for simple spoken explanations, clickable diagrams, numbered request or event flows, component responsibilities, failure scenarios, and compact interview revision. Produce a downloadable HTML file by default rather than deploying with Sites.
---

# FDE HTML Explorer

Turn a system-design case into an interactive interview workbench. Deliver **one standalone `.html` file**, with content, CSS, JavaScript, and diagrams embedded. Keep it close to a guided conversation, not a textbook.

## Output contract

- Generate `<use-case>_fde_explorer.html`, opening directly from disk without a server, installation, API, network access, or build step.
- Use the bundled renderer to preserve this format. Adapt content and topology; do not force every system into the same seven-component chain.
- Support one system by default and a system selector when several are requested.
- Do not create, update, publish, or deploy a Site unless separately requested. Do not imply a local HTML file has authentication or access control.
- Save the completed HTML through the environment's normal file-saving workflow. Return its link and what was tested.

## 1. Ground the case

Read supplied sources and current named files before making source-specific claims. Preserve the actual purpose and architectural boundaries.

With no source, create a small **representative design**, label it illustrative, and state the assumptions that shape the flow. Do not fabricate unavailable pages, rules, quotations, measured results, throughput, prices, or SLAs.

Distinguish source-supported patterns, design choices added to the example, and illustrative inputs/outcomes. Explain the distinction in **Content & sources**. Name real source files or URLs. Do not claim full source coverage when only selected sections were read.

## 2. Shape the story

Use one consistent person, request, event, or release candidate throughout each scenario. Write in simple spoken English: “First we check who is asking.” Name a component, then explain its purpose. Expand acronyms briefly when they first matter. Avoid filler and deep theory.

Create normally **5–9 numbered stages**, using the count the case needs. For asynchronous systems follow an event or job to its completion rather than pretending it is synchronous chat.

For every stage provide:

- **Title and component:** a concrete action and its owner.
- **What it does:** this example's execution now, normally 2–3 short sentences.
- **Why it exists:** the need or failure it addresses, normally 1–2 sentences.
- **What happens next:** the actual destination or terminal outcome.
- **Checks:** important deterministic controls and semantic assessments; no invented LLM checks.
- **Example:** small input/output payloads labelled as illustrative.
- **Diagram nodes:** components active at this stage.

Include a normal scenario and a meaningful failure, uncertainty, or approval scenario when applicable. Choose a real architectural boundary. Match the flow and diagram: denied access stops before retrieval; required approval stops before a write; missing evidence does not become a grounded success; blocked releases do not deploy.

## 3. Preserve these views and interactions

1. **Overview:** purpose, request, scope, source/adaptation notes.
2. **Explore flow:** scenario selector, clickable architecture, active stage, visited components, previous/next/reset, numbered stage picker, and pauseable automatic stepping.
3. **Stage details:** What & why, Checks, and Example tabs.
4. **Interview revision:** 60–90 second spoken answer, one-line flow, functional/non-functional requirements, 2–3 discovery questions, one tradeoff, one failure, and scale/latency/cost/evaluation talking points.
5. **Sources and local progress:** provenance, browser-local reviewed state, copy-answer, printable revision, and keyboard controls.

Keep revision approximately **70% rapid recall and 30% explanation**. Preserve important concepts by compression. Aim for one printed page when practical; do not promise page count without checking it.

Use a light interface, muted purple accents, clear type, spacious cards, responsive layouts, visible focus, keyboard operation, and reduced-motion support. Prefer legible labels and a scrollable map to tiny text.

## 4. Draw the real topology

Use the bundled inline SVG renderer. Do not use generated imagery or a network-loaded diagram library.

- Supply explicit nodes and directed edges for the main flow, parallel work, dependencies, stores, approvals, and side effects where relevant.
- Keep connectors clear of labels and interiors. Use at most five components horizontally; use multiple rows for larger systems.
- Map each selectable node to a stage. Mark skipped components and remove inactive execution edges in failure scenarios.
- Highlight the correct components per stage. Allow different scenario stage counts and graph edges.
- Show observation paths separately from business actions. Distinguish ingestion, indexing, and serving when included.
- Do not add agents, queues, caches, or databases just to fill a template.

## 5. Apply only relevant boundaries

- **Permissions:** derive trusted identity/scope before sensitive access; enforce ACLs in the data path.
- **RAG:** separate search relevance from answer support; preserve evidence IDs; handle insufficient evidence honestly.
- **Actions:** separate recommendation, policy authorization, and execution; check authoritative receipts; bound loops/retries; prevent duplicate writes.
- **Evaluation:** distinguish exact checks from semantic judgement, offline suites from online signals and release decisions; calibrate judges and check critical slices where needed.
- **Scale and cost:** bound admitted work and concurrency, measure end-to-end latency, and attribute retries, tools, and model operations to the request. Label sizing assumptions.

## 6. Build the HTML

Read [the content contract](references/data-contract.md). [references/enterprise_rag_fde_explorer.html](references/enterprise_rag_fde_explorer.html) shows a finished explorer; use it for format only, not as a source of facts. Write temporary JSON following it. Use plain strings, not executable HTML.

From this skill directory run:

```bash
python3 scripts/build_explorer.py \
  --data /absolute/path/case-content.json \
  --output /absolute/path/use_case_fde_explorer.html
```

The builder validates content and embeds it in `assets/explorer-template.html`. Change the template only when a requested interaction cannot be expressed by the contract. Keep changes self-contained.

## 7. Verify and deliver

Check for external scripts/styles/fonts, module imports, fetch calls, and local asset dependencies. Verify untrusted source text cannot terminate the JSON script or execute as HTML.

Exercise every scenario's first/intermediate/final stages, diagram selection, detail tabs, reset, revision, sources, and reviewed state. Confirm pending or failed paths never claim a successful action. Check keyboard controls and print styles.

Use supported browser tooling when available. Otherwise run syntax, schema/content, and DOM-level interaction checks and disclose that visual browser QA is unverified. A schema check is not browser testing.

Return the HTML link, the covered case, and material verification limits. Do not deploy it.
