---
name: course-content
description: >-
  Create or rewrite forwarddeployedprep.com course lessons in the approved interactive course-page format. Preserve source concepts, evidence and diagrams; teach mechanisms through worked traces and separately explained alternatives; export offline Markdown and HTML with the bundled renderer. Use for a Forward Deployed lesson URL, course lesson, module, or a new course topic.
metadata:
  argument-hint: <lesson URL | source path | module/lesson | topic> [review | edit]
---

# Course content

Use the approved page as the visual and teaching reference for other forwarddeployedprep.com lessons. Keep the frame and component behavior consistent. Adapt the examples, headings, diagrams and optional interactions to the topic.

## Read before drafting

1. [Approved format](references/approved-format.md): the exact approved HTML, its original source URL, the design contract and transfer rules.
2. [Source fidelity](references/source-fidelity.md): inventory concepts, facts, diagrams, comparisons, caveats and checks across every user-supplied reference.
3. [Editorial explanation](references/editorial-explainer.md) and [Voice](references/voice.md): the teaching sequence and theory-only prose.
4. [Components](references/components.md) when a stepper or comparison earns its place. [Validation](references/validation.md) before delivery.

Inspect `standalone/references/example-lesson.html` visually and read its paired Markdown. This is the approved target, including both edge-versus-node comparison diagrams restored at the user's request. It replaces the older example lesson. Do not substitute a theme, an earlier adaptation or the unmodified live source page for this target.

Use No AI Slop and Hallmark when available. Hallmark checks the approved house style; it does not choose a new theme or restructure the approved frame. The skill is self-contained if those companion skills are unavailable. No global installation, publication, commits or messages are implied.

## Select the workflow

- A URL or supplied source file means adapt that lesson into the approved format. Fetch the actual article and its diagrams. Use a supplied source snapshot when needed, with its provenance recorded. Do not ask whether to proceed when the user already requested the adaptation.
- A topic without source means create a lesson with cited primary references, labelled illustrations and the same frame. Never transplant the refund question or LangGraph content into an unrelated topic.
- In a course repository, read its applicable instructions and [Course repository](references/course-repository.md). Preserve exact curriculum concept headings, importer hooks, notebook slots and navigation. Export outside the theory folders through `scripts/export_lesson.py`.
- `review` writes reviewable drafts and exports outside the source repository. `edit` changes the authorised source pages. Preserve existing site routes, labs and protected assets. A source URL alone does not authorise publishing to the live site.

## Plan the source coverage and teaching

Inventory every source teaching item and every visual from all relevant inputs. That includes diagrams introduced by another supplied adaptation. Record a coverage entry for each item: source location, teaching content, output anchor, status and evidence for any authorised omission. Renamed headings are welcome when clearer; repository contract headings remain exact. A source section may span several output sections, but a mention does not preserve a worked explanation.

Use a natural learning sequence: a concrete failure or need; intuition and definitions; architecture; one request traced through decisions and state; genuine alternatives taught separately; comparison and decision rule; failure diagnosis, limits and checks. Reorder non-contract sections when helpful. Avoid a fixed count of headings, figures or controls across unrelated topics.

For genuine architectural alternatives, retain or create one labelled diagram for each approach, beside its own explanation. Use the same input to expose different state/output effects. Then compare and state when each approach fits. A switcher or comparison table supplements those diagrams. It never substitutes for them.

Choose interactions by the concept: a stepper for a process with meaningful stages; a switcher when alternative choices change the evidence, state or result; no widget when static explanation is clearer. A page without an architectural alternative does not need a comparison switcher. A stepper need not have six stages, and a switcher need not have two modes. Label scripted examples and fictional data.

Create a lesson manifest using `examples/manifest.schema.json`. Include stable output anchors for all source items and an asset hash for every preserved diagram payload. Mark source concepts and claims as reviewed only after substantive comparison. For a published source, record its URL. Include required figure and component IDs in the manifest to catch an accidental omission during export.

## Write and build

Write frontmatter and theory Markdown using [Standalone](references/standalone.md), with descriptive headings, numbered captions, source links, the original notebook destinations and conceptual self-checks. Render code mechanisms as traces or field tables. Mermaid is the only allowed code fence. Keep source numbers and uncertainty; additions are labelled and grounded. Keep the full prose, including every interaction panel, within the default 2,500-word budget. Cut repetition and additions before source concepts; an explicitly authorised higher limit must be recorded in the manifest.

Author the components as static HTML in the Markdown using [Components](references/components.md). All explanations must be present before scripting. The renderer embeds the shared styles, generic interactions, fonts and light/dark Mermaid images automatically. No post-build patching is needed.

Run from any working directory, replacing `SKILL_DIR` with this skill's actual path:

```bash
python3 SKILL_DIR/standalone/scripts/build_site.py lesson.md lesson.html
python3 SKILL_DIR/scripts/validate_lesson.py lesson.md lesson.html lesson.manifest.json
```

The Python dependencies are in `requirements.txt`. The renderer checks for its Mermaid/font dependencies and installs missing npm packages in a cache. Existing `CONTENT_WRITE_CACHE` and `CHROME_PATH` settings are supported. Read [Validation](references/validation.md) for browser verification and visual comparison. A failed check blocks a claim of completion; correct the issue and rerun the affected checks.

For other pages on the live site, adapt content in the source/import pipeline and integrate the shared CSS/reader behavior into its maintained template. Match the approved article design while preserving the site's genuine navigation. Do not hand-edit generated routes or replace the site's framework with this standalone exporter.

## Required rewrite tracking

After rewriting any module or lesson belonging to this course, update `/Users/sourav/Github_Repos/rag-agents-engineering/REWRITE_TRACKER.md` before delivery. This includes partial-module rewrites, review drafts and HTML-only exports even when the source README is unchanged. Resolve the module from the lesson path or curriculum metadata. Output format and destination do not exempt a course rewrite from tracking.

Use `scripts/tracker.py`, never hand-edit the tracker table. Follow [Course repository, step 8](references/course-repository.md#8-update-the-tracker-then-report) for the command and status mapping. Record which lessons were rewritten, artifact paths, validation results and remaining work in the note. Read back the affected row and include its status in the final report. If updating fails, report the failure and do not claim tracking is complete. Unrelated standalone topics have no module row to update.

## Delivery gate

Before delivery, compare source coverage and the approved component pattern. Confirm every inventoried diagram remains, especially a pair that distinguishes alternatives. Test every stage/mode, keyboard use, disabled controls, internal links, mobile/light/dark, offline assets and the no-script fallback. Inspect every figure. Do not call a deterministic rebuild an independent test of newly authored prose.

For a new or substantially revised skill package, use an independent agent to author or adapt a different lesson with only the packaged instructions and source. Keep it in an isolated workspace and review the resulting lesson. A second topic tests transfer beyond the reference; the saved reference rebuild tests the renderer.

Deliver the Markdown, self-contained HTML, source coverage and actual check results. For a package revision, also deliver the ZIP, the reference rebuild and the comparison report. Never promise that any skill can eliminate all future mistakes. State what was verified and what still requires editorial judgment.
