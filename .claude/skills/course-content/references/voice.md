# Voice and teaching

How the reader-facing prose reads, in every mode. `contracts.md` and `CLAUDE.md` fix the exact headings, header lines, navigation and build contracts; never break them for a nicer page. Run `no-ai-slop` over the result; where it conflicts with this file, this file wins, and the repo's contracts win over both.

## The reader

Write for a beginner and an experienced engineer at once. The beginner follows the page without looking terms up. The experienced engineer finds the mechanism, the trade-offs and the production consequences. After reading, either one can explain the concept in their own words.

## Theory only: no code

The pages teach concepts and engineering decisions. The notebooks carry the code, and their Markdown cells explain it. So a page has:

- **No code blocks.** The only fenced blocks are ` ```mermaid `. `scripts/protect.py` fails a page that has any other fence.
- **No notebook walkthroughs**: no setup, commands, installs, environment or provider configuration, helper functions, decorators, parser internals, SDK parameters, model versions or protocol syntax that only one example uses.
- **No notebook links in the body**, except an existing source notebook section retained in a standalone adaptation when no importer creates it (`source-fidelity.md`). Notebooks appear only in the lesson's italic header line (repository navigation, load-bearing). No `### Practice notebook` or "open the notebook and run…" sections; turn a notebook exercise into a standalone conceptual question.
- **Mechanisms stay.** Explain tool schemas, observations, dependent actions, validation, state, retries and stopping conditions as ideas. Show what moves through a system with a table (inputs, outputs, what changed) or a diagram, not with source code or raw JSON.
- **Numbers stay, sourced.** Get a figure by running the notebook's own deterministic code or a lab in the scratchpad, then quote the result in prose or a table and say where it came from. Never show the code that produced it.

## Shape

`lesson.md` describes the learning outcomes and repository contracts. approved-format.md governs the presentation, while the source determines non-contract section titles and order. In short: open on a concrete failure in the source's running example, define the idea, show the mechanism with a figure, trace an example in a table, plant failures and name them, do the arithmetic, compare genuine alternatives, apply the decision to the same example, state the limits. No `### Step N` headings: sections are named for what they teach.

## Sentences and paragraphs

- Conversational and precise, like an engineer explaining to a colleague. "We" when reasoning or building together, "you" for advice; never "I".
- Paragraphs of 1 to 4 sentences. One idea per sentence. A one-sentence paragraph for a key point.
- Define each new term in plain words the first time, in bold, then use the precise term consistently. Expand acronyms once.
- Every abstract statement is followed within two sentences by an example from the running scenario or a real system.
- Name failure modes and patterns with a short, memorable label and reuse it.
- Exact figures over round claims ("959M rows in a 28.6 GB file", not "a large dataset").
- At most one analogy per major section, and only one that maps onto the mechanism.
- Options and taxonomies as `- **Label**: one-line meaning.`, items parallel.
- Introduce each table or diagram with one sentence that says what it shows, then the artefact, then one sentence on what it means.
- Callouts as blockquotes with a plain bold label and no emoji, at most one per ~400 words: `> **Key distinction:**`, `> **Pitfall:**`, `> **Interview tip:**`.
- Report negative and inconclusive results as plainly as wins.
- End a section with a sentence that sets up the next one, as a statement.

## Banned

En and em dashes (write "20 to 50", "M14 to M16"); rhetorical questions; "not X, it's Y"; faux-insight setups and colon reveals; closing aphorisms; filler openers; hype words; calling anything "easy" or "obvious"; textbook or corporate phrasing; invented metrics, quotes, citations or API claims; repeated summaries; identical section shapes across a page; copying text or figures from other courses or books.

## Links and sources

- The page reads fully without opening any link.
- At most one link in an explanatory paragraph; descriptive link text, never a bare `M23` or `05a`.
- Other modules by number in prose, linked by relative path to their theory module page when one exists.
- Cite a named, dated source for a non-obvious claim; paraphrase it. Verify claims about a library against its installed source in this repo's environment, and anything that moves (APIs, model names, prices, benchmarks) against current docs (Context7 or web search).
- Keep the inline link to a lab beside its `<!-- lab: ... -->` marker (a test needs it).

## Quality gate

- [ ] The page opens on a concrete failure in the running example and follows `lesson.md`.
- [ ] Every figure and table is introduced, numbered and captioned; every named failure mode is reused by name.
- [ ] No `### Step N` headings.
- [ ] Every exact `##` concept heading from `concepts:` is on exactly one page.
- [ ] No fenced block other than Mermaid. Course notebook links stay in their header/generated slot; standalone adaptations may retain the source notebook section.
- [ ] One example runs through the whole page; every number is sourced or labelled *Illustrative*.
- [ ] A contrast, a decision rule and a named failure mode are present where the topic has them.
- [ ] A beginner meets no undefined term; an expert finds the trade-offs.
- [ ] Read aloud, it sounds natural; no section repeats another.
