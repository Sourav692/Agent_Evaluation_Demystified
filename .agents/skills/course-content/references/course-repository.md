# Course repository workflow

This reference preserves the course resolver, importer, tracker and repository-specific commands. Read it only when working in that repository. The current SKILL.md, approved-format.md, components.md and source-fidelity.md govern presentation, editorial freedom, diagram coverage and optional component counts when older wording below differs. Follow actual repository instructions when files or paths have changed.


One skill for all theory writing. The input is `$ARGUMENTS`. `CLAUDE.md` → Theory pages holds the repository rules; this file is the procedure, and the references hold the detail:

| File | Read it for |
|---|---|
| `references/contracts.md` | Load-bearing page shapes (module page, lesson page), Mermaid/SVG/animated-diagram/lab formats, browser verification. Create and rewrite. |
| `references/lesson.md` | The lesson shape: sections in order, what goes inside a concept section, how code becomes tables and figures. Every mode. |
| `references/voice.md` | The reader, the theory-only rule, sentence rules, the quality gate. Every mode. |
| `references/source-fidelity.md` | Source inventory, heading flexibility, diagram preservation, additions and coverage verification. Every source-derived mode. |
| `references/rewrite.md` | Coverage inventory, protected blocks, review vs edit. Rewrite mode. |
| `references/standalone.md` | Frontmatter, the system-design template, the HTML builder, track emphasis. Standalone mode. |

## Mandatory source fidelity

Read `references/source-fidelity.md` before editing or generating any source-derived lesson. Inventory the source concepts, examples, evidence, caveats, checks and diagrams, then produce a source-to-output coverage matrix. Descriptive headings may be renamed and sections reorganised when this improves teaching, provided every source item remains explicit and traceable. Preserve exact repository contract headings and protected assets. Useful additions are encouraged when labelled and grounded. Do not use an earlier adaptation as the source of truth. Missing source concepts or diagrams fail the build; changed editorial wording does not.

## Pick the mode

| Input | Mode |
|---|---|
| A module (`14`, `M14`, `embeddings`) or a lesson/topic (`11.3`, `M13 4`, `chunking "semantic chunking"`) whose page is missing or has gaps | **create** |
| The same, or a theory README path or site URL, plus `rewrite` (`review` by default, `edit` to change files) | **rewrite** |
| `--standalone <track> <topic>`, or a topic that is not one of the 46 modules | **standalone** |

When a page exists and the user did not say `rewrite`, ask once whether to extend it (create) or rewrite it. If the mode or target is still unclear, ask one question.

**Rules for every mode.** No code blocks and no notebook links in the body (`voice.md` → Theory only), except an existing notebook section retained in a standalone source adaptation with no importer. Never invent a number, quote, benchmark or API: every figure comes from a notebook run, a lab you built and verified, or a cited source. The running example is the fictional Larkspur Cloud handbook (pricing, refunds, exports, outages, server sizing).

## 0. Set up

1. Load `no-ai-slop` (plus `hallmark` when building HTML or a lab). Load `napkin` only when available in the target repository. Read `CLAUDE.md` → Theory pages, `references/lesson.md`, `references/voice.md`, the mode's reference, and skim `standalone/references/example-lesson.html` for the target look.
2. Resolve course targets:
   ```bash
   uv run python .claude/skills/course-content/scripts/resolve.py <module> [<lesson or topic>]
   ```
   It prints the module's `why`, objectives, concepts and which page holds each, lessons with theory folders and notebooks, existing pages, labs and animated diagrams, neighbours, and the matched lesson or concept. No single match: show the closest options and ask. Use its paths; never build folder names by hand.
3. Read what exists: the module's theory pages, `<part>/<module>/README.md`, `lab/README.md`, and the M10 reference (`p04_rag_foundations/m10_rag_lifecycle/mandatory/theory/`: module page, a lesson page, `diagrams/lifecycle.anim.html`, the top-k lab).

Rewrite mode continues in `references/rewrite.md`, then step 7. Standalone mode continues in `references/standalone.md`. Create mode follows steps 1 to 8.

## 1. Ground the content in the notebooks

Open every mandatory notebook the resolver lists, and the optional ones a concept depends on. For each lesson note the mechanisms shown, the numbers the notebook prints or states, the trade-offs, and which `concepts:` it teaches. Notebooks ship without outputs: get numbers by running their deterministic code in the scratchpad. Claims without evidence stay out. The page explains what the code demonstrates; it never reproduces the code.

## 2. Plan, and say the plan before writing

State the plan briefly. Proceed when the user has already authorised the module or lesson work; ask only for information or authority that is genuinely missing:

- **Concept to lesson map.** Each `concepts:` entry goes to exactly one lesson page, the one that teaches it. A lesson whose notebook is a build with no concept of its own (an app, a worked project) gets a **project page** (`lesson.md` → Project page), never a *planned* row. A lesson page has at least one `##` section.
- **Diagrams per page.** One mental-model diagram on the module page; one or two per lesson where a picture beats prose. Mermaid first; SVG only for spatial layouts and charts Mermaid cannot draw. Animate only processes over time, usually the mental model plus one more.
- **The lab.** At most one per module unless two lessons each have a parameter worth playing with. It earns its place when one control changes a number the prose argues about. Name its lesson and section.
- **Running example.** The handbook area and golden questions, and one concrete request or failure to follow through each lesson.
- **Per lesson:** the subtitle, the concrete failure it opens on, its sections in `lesson.md` order with their headings, the figures and tables (numbered), the planted failures and their names, any claims it will settle, and the decision rule.

Topic mode also states which module-page sections change (Lessons row, TL;DR bullet, mental model, How it connects, interview questions, takeaways); nothing else is rewritten.

## 3. Write the pages

Contracts from `contracts.md`, shape from `lesson.md`, prose from `voice.md`.

- **Module page** `<theory>/README.md`: title, meta line, intro with the "Each idea has a page…" sentence, running-example paragraph, `## TL;DR`, `## Mental model`, `## Lessons`, `## Interactive lab`, `## How it connects`, `## Interview Spotlight: 5 Questions You Might Get Asked`, `## Key Takeaways`, footer.
- **Lesson page** in the folder `resolve.py` gives (`mandatory/theory/` or `optional/theory/`): title, header line, `<!-- subtitle: … -->` and `<!-- format: approved -->` on the next line, then the `lesson.md` sections with each `## <exact concept>` among them (What you'll learn opens the first section), `## Key Takeaways` (three bullets, four when the page has four or more concepts), `## Check yourself`, footer. No `### Step N` headings.
- **Check yourself:** three `<details>` blocks (`<summary>N. Question?</summary>`, blank line, 2 to 4 sentence answer, blank line, `</details>`): the mechanism, an application to the page's example or numbers, and a diagnosis or decision. Plain-text questions; answers use only the page.
- **Interview Spotlight:** five production scenarios on the running example, never "what is X": at least an incident, a design trade-off, a measurement or monitoring question and an edge case, each with four "What a strong answer covers" bullets.

Topic mode: write or extend only the target lesson page, flip its Lessons row from planned to linked, and change only the module-page sections the plan named. Moving a concept removes its old heading. Keep neighbouring footers pointing at real neighbours.

## 4. Diagrams

Follow `contracts.md` → Mermaid, SVG diagrams, Animated fragment. Readable at 614px: short edge labels, detail inside nodes with `<br/>`, no many-into-one convergence, yes/no chains instead of one question with four long answers. SVGs: own sheet background, Almanac hex palette, `<title>` and `<desc>`, text 13px or more, plotted values computed. Animated fragments: copy `lifecycle.anim.html`'s structure, at most eight steps, the lab's real numbers or none, unique marker ids.

## 5. The lab

Copy the structure and stylesheet of M10's `top-k-retrieval-lab.html`, then design this lab's own control and output. Keep the Hallmark stamp, Almanac tokens, Google Fonts as the only external request, `overflow-x: clip`, eight control states, `:focus-visible`, reduced motion, a live reading paragraph, and embedded mode (`contracts.md` → Lab file). Port small algorithms exactly and compare against the Python library on every control position; keep the comparison result for the report. Every number the prose quotes from the lab must be one the lab prints. Mark the spot with `<!-- lab: interactive/<name>.html -->` and link it inline in that section.

## 6. Edit the prose

Run the `voice.md` quality gate, then `no-ai-slop`, over every page.

## 7. Build and verify

```bash
uv run python .claude/skills/course-content/scripts/protect.py [--rewrite] <changed pages>   # no code blocks; rewrite: diagrams unchanged vs HEAD
uv run python scripts/build_curriculum.py
uv run pytest -q
uv run python scripts/check_links.py
uv run python .claude/skills/course-content/scripts/export_lesson.py <changed lesson pages>     # the .md + .html pair
```

The export writes `site-export/<track>/<module>/<NN>-<lesson>.md` (git-ignored) with frontmatter from `curriculum.yaml` and `docs/fde-site-slugs.yaml`, then renders the `.html` beside it with `standalone/scripts/build_site.py` (`--md-only` skips it; `--out DIR` moves it). Open one `.html` at 1254px and 390px, light and dark, and look at every diagram.

Then the browser check in `contracts.md` → Verification: serve the repo with `python3 -m http.server <port> --bind 127.0.0.1`, open the module's `index.html` at 1280px and 390px, and confirm every Mermaid diagram rendered, none below 75% scale, animations step and autoplay, the lab frame sized itself, no sideways scroll. Lint copies outside the repo (sloplint writes `.hallmark/` beside its input):

```bash
S=<scratchpad>/lint; rm -rf $S && mkdir -p $S && cp -R p[0-9][0-9]_* $S/
cd $S && node ~/.claude/skills/hallmark/scripts/sloplint.mjs <part>/<module>/mandatory/theory/index.html --genre editorial --render
node ~/.claude/skills/hallmark/scripts/sloplint.mjs <part>/<module>/*/theory/*/interactive/*.html --scope app --render
```

`--render` needs `HALLMARK_PUPPETEER` pointing at a `puppeteer-core` install. Fix every FAIL; page-level waivers live in `scripts/site/theory.template.html`. Never hand-edit a generated `index.html`. Stop the server; delete `.playwright-mcp/` and screenshots in the repo. Rewrite in review mode skips this step, except the export: run it with `--out <scratchpad>` on each draft as `<draft>=<lesson README>` so the user can open the HTML.

## 8. Update the tracker, then report

Every course-module run ends by updating `/Users/sourav/Github_Repos/rag-agents-engineering/REWRITE_TRACKER.md` through its script before delivery. This includes create, rewrite review, rewrite edit, a single lesson, a partial module and an HTML-only export whose source README is unchanged. Resolve the module from its lesson path or curriculum metadata. A standalone output format does not exempt content belonging to this course. Unrelated standalone topics have no module row. Never hand-edit the table.

Run from `/Users/sourav/Github_Repos/rag-agents-engineering`:

```bash
uv run python .claude/skills/course-content/scripts/tracker.py --set <module> "<status>" [--pr "#N"] [--note "<one line>"]
```

| What the run did | Status |
|---|---|
| Review draft or HTML-only rewrite delivered; source pages unchanged | `Review draft` |
| Pages edited or written, not yet in a PR | `In progress` |
| PR opened | `In PR` (add `--pr`) |
| PR merged and the page is on forwarddeployedprep.com | `Live` |

The note records the rewritten lesson numbers, artifact paths, validation results and remaining work. For example: "28.1 HTML review: 01_retriever_as_a_tool_grade_then_rewrite_in_langgraph.html; browser checks passed; source unchanged; 28.2 and 28.3 pending." Read the existing row first. Preserve existing PR references and relevant notes. If the module is already `In PR` or `Live`, preserve that status for a new review draft and describe the pending revision in the note.

The script recomputes Lessons, Pages and New style from source pages. An HTML-only draft must not increase New style or mark the whole module as applied. A module is only `Live` when New style equals Pages and publication is verified. After running the command, read back the affected row to confirm its status, date and note, then show it in the final report. A failed tracker command must be reported rather than treated as a successful update.

Report both paths of every exported pair, then what was written or changed (pages, concepts per lesson, diagrams static and animated, the lab and its verification), which lessons got project pages, check results, anything unconfirmed, and in rewrite mode the flags from `rewrite.md` → Report. Do not commit unless asked. Record new gotchas in `.claude/napkin.md`.

Read `references/editorial-explainer.md` for supplementary teaching improvements after source coverage is verified.
