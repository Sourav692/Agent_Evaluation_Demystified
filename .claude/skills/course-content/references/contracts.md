# Page formats

Everything here defines the build-sensitive page structure used by M10 (`p04_rag_foundations/m10_rag_lifecycle/mandatory/theory/`). When in doubt, copy its structural contracts, not its prose density. Apply `voice.md` to the learner-facing body within those contracts. `build_theory_html.py` parses some of these lines, so the marked ones are load-bearing.

## Module page: `<part>/<module>/mandatory/theory/README.md`

```markdown
# M14 Theory: Embeddings and model selection                     ← "# M<NN> Theory: <name>"; the HTML h1 uses the text after ": "

*Part IV · RAG Foundations: Ingestion & Indexing · [Module README](../../README.md) · [All theory pages](../../../../THEORY.md)*
                                                                 ← load-bearing: "*Part <roman> · <part title> · [Module README](…)"

<Two or three sentences on what the module is about.> The M14 notebooks build on four ideas: <the concepts in plain words>. Each idea has a page in the folder of the lesson that teaches it, listed under [Lessons](#lessons). This page has the overview, the interview questions and the takeaways.
                                                                 ← the "Each idea has a page…" sentence is matched and removed in index.html; keep it word for word

<One paragraph naming the running example: which part of the Larkspur Cloud handbook, the golden questions.>

## TL;DR

- 4 or 5 bullets, one claim each, with the module's key numbers.

## Mental model

```mermaid
flowchart LR
    …
```
<!-- animated: diagrams/<name>.anim.html -->                       ← only if this diagram has an animated version

<One paragraph: what the diagram means and the one thing to remember.>

## Lessons

| Lesson | Topic | Theory |
|---|---|---|
| 14.1 | <lesson title from curriculum.yaml> | [<Concept or section>](<lesson folder>/README.md#<anchor>)<br>[<Second>](<lesson folder>/README.md#<anchor>) |
| 14.2 | <lesson title> | *planned* |
                                                                 ← load-bearing: index.html inlines the linked lesson pages in this order

## Interactive lab

[**<Lab title>**](<lesson folder>/interactive/<name>.html): open the file in a browser. <Two or three things to try, in the order that shows the payoff.>

## How it connects

- **Before:** <earlier modules this builds on, by number, linked to their theory module page when one exists>.
- **Next:** <later modules, same style>.

## Interview Spotlight: 5 Questions You Might Get Asked

*Production questions of the kind asked in applied AI engineering interviews.*

### 1. <A production scenario on the running example, one or two sentences, ending in a question.>

**What a strong answer covers:**
- <four bullets: what to check first, the trade-off, the measurement, the guard>

### 2. …                                                         ← five in all: an incident, a design trade-off, a measurement or monitoring question, an edge case, one more

## Key Takeaways

- 4 bullets, each a rule the reader can apply.

---
*Previous: [M13 Chunking](../../p05_ingestion_and_indexing/m13_chunking/README.md). Next: M15 Vector stores (no theory page yet).*
                                                                 ← load-bearing: "---" then "*Previous: … Next: ….*" as the last lines
```

Without a lab, drop the `## Interactive lab` section. Section anchors are GitHub's: lower case, punctuation dropped, spaces to hyphens (`Top-k` is `#top-k`).

## Lesson page: `<lesson folder>/README.md`

```markdown
# M14.2 Theory: <lesson title from curriculum.yaml, exact>

*[M14 theory](../README.md) · Lesson 14.2 · Notebooks: [`02a_x.ipynb`](../../notebook/02a_x.ipynb), [`02b_y.ipynb`](../../../optional/notebook/02b_y.ipynb) (optional) · [All theory pages](../../../../../THEORY.md)*
                                                                 ← load-bearing: " · Notebooks: … · [All theory pages]"; leave out "· Notebooks: …" when the lesson has none
<!-- subtitle: <one line naming what the page resolves> -->         ← invisible on GitHub; export_lesson.py uses it
<!-- format: approved -->                                          ← load-bearing: marks a page rewritten in the approved format (references/approved-format.md); tracker.py counts it

## <Descriptive heading for the problem, or the first concept>

> **What you'll learn**
>
> - **Explain** …

<Recap sentence, then the concrete failure. The rest follows references/lesson.md: figures and tables numbered and captioned, no code blocks, no `### Step N` headings. Mandatory notebooks first in the header, optional ones marked "(optional)".>

## <Concept, exact text from concepts:>

<!-- lab: interactive/<name>.html -->                              ← only in the lesson that owns the lab, where it should appear

## <Further concepts, Choosing …, In practice: …, Limits, References>

## Key Takeaways

## Check yourself

---
*Previous: [14.1 <title>](../01_<slug>/README.md). Next: [14.3 <title>](../03_<slug>/README.md).*
```

First lesson page: `Previous: [M14 overview](../README.md)`. Last: `Next: [M14 interview questions](../README.md#interview-spotlight-5-questions-you-might-get-asked)`. Skip planned lessons: the footer chains lesson pages that exist. The body starts at the first `## `: anything between the header line and it is dropped from index.html, so do not put intro text there.

## Mermaid

- `flowchart LR` for pipelines, `flowchart TD` for decision chains, `sequenceDiagram` for call loops, `quadrantChart` for a two-axis trade-off.
- `index.html` draws each diagram at the column width (about 614px). A chart wider than 4/3 of that is redrawn in the other direction, and if still too wide it scrolls at 75%. Design for that width: short edge labels (`yes`, `no`, `Markup`), detail inside nodes with `<br/>`, three to four nodes per row, no subgraph with more than four nodes in a line.
- Never let many leaves converge on one node (dagre puts all of them on one row). Put the shared next step in the paragraph under the diagram.
- A question with four long answers becomes a chain of yes/no diamonds (M13's mental model).
- Quote node text containing `:`, `(`, `/` or `?` (`A["Retrieved chunk:<br/>refund-window"]`).

## SVG diagrams

Own `viewBox`, a sheet background rect (`#e5eaef`), ink `#060e15`, second ink `#182027`, muted `#3b434b`, rule `#a1a9af`, magenta `#970d63` for the one thing that matters, pale magenta `#f0ccdc` for its fill. `<title>` and `<desc>` first (index.html uses `<desc>` as the alt text). Hanken Grotesk for labels, IBM Plex Mono for numbers. Reference from the lesson page as `![<alt>](diagrams/<name>.svg)`.

## Animated fragment: `diagrams/<name>.anim.html`

Canonical: `p04_rag_foundations/m10_rag_lifecycle/mandatory/theory/diagrams/lifecycle.anim.html` (stages appearing) and `05_the_rag_lifecycle_and_a_measured_baseline/diagrams/baseline-loop.anim.html` (a marker travelling a loop).

```html
<!-- Animated version of the <name> flowchart in ../README.md, used by index.html. … -->   ← dropped on build
<figure class="anim sheet" aria-labelledby="anim-<name>-cap">
  <div class="anim__canvas" tabindex="0" aria-label="<name>, scrolls sideways on a narrow screen">
    <svg viewBox="0 0 800 352" role="img" aria-labelledby="anim-<name>-title anim-<name>-desc">
      <title id="anim-<name>-title">…</title><desc id="anim-<name>-desc">…</desc>
      <defs><marker id="ah-<name>" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path class="ah" d="M0 0 L8 4 L0 8 z"/></marker></defs>
      <g class="n-1"><rect class="box" …/><text class="label" …>Load</text></g>    ← n-N: lit while step N is current
      <path class="edge e-2" d="…" marker-end="url(#ah-<name>)"/>                   ← e-N: lit while step N is current
      <g class="in-3">…</g>                                                           ← appears at step N and stays
      <g class="mv-6" style="--from: translate(430px, -180px)">…</g>                  ← moves in from that offset at step N
      <circle class="tok" cx="0" cy="0" r="7"/>                                       ← optional marker, placed by data-tok
    </svg>
  </div>
  <div class="anim__controls" hidden>
    <button class="anim__btn" type="button" data-act="prev">Previous</button>
    <button class="anim__btn" type="button" data-act="play" aria-pressed="false">Play</button>
    <button class="anim__btn" type="button" data-act="next">Next</button>
  </div>
  <ol class="anim__steps" id="anim-<name>-cap">
    <li><button type="button" data-tok="30,36">Load</button><span>The loader reads the handbook into Documents.</span></li>
  </ol>
</figure>
```

Classes for shapes and text: `lane`, `lane-label`, `box`, `label`, `small`, `fig` (mono figures), `edge`, `edge dashed`, `doc`, `line`, `chunk`, `vec`, `hit` (magenta fill), `hit-line`, `tok`. Step-name buttons stay one or two words (sloplint fails long control labels). SVG text 13px or more at an 800px viewBox. The finished frame is the default: it is what no-JS and reduced-motion readers see, so it must read on its own.

## Lab file: `<lesson folder>/interactive/<name>.html`

Canonical: `p04_rag_foundations/m10_rag_lifecycle/mandatory/theory/02_indexing_from_scratch_with_tf_idf_and_nearest_neighbours/interactive/top-k-retrieval-lab.html`. Its title is the lab's name everywhere (frame caption, module page button). Its stamp's waivers and dropped-id lines are part of the Hallmark record; write this lab's own. The embedded-mode block:

```html
html.embedded { --gutter: var(--space-2xs); }
html.embedded .bar, html.embedded .intro { display: none; }
html.embedded main { padding-block: var(--space-2xs); }
html.embedded, html.embedded body { overflow-y: hidden; }
html.embedded .layout > .stack { display: contents; }     /* then order the parts so control and output share a screen */
</style>
<script>if (window.self !== window.top) document.documentElement.classList.add("embedded");</script>
…
// at the end of the lab script
if (document.documentElement.classList.contains('embedded') && 'ResizeObserver' in window) {
  new ResizeObserver(() => parent.postMessage({ labHeight: document.body.getBoundingClientRect().height + 2 }, '*')).observe(document.body);
}
```

## Verification

Run in the browser at 1280x900 and 390x844 (serve the repo over `http.server`; Playwright cannot open `file://`):

```js
// all diagrams drawn, none shrunk below 75%, no page overflow
const pres = [...document.querySelectorAll('pre.mermaid')];
({ drawn: pres.filter(p => p.querySelector('svg[aria-roledescription]')).length, of: pres.length,
   scales: pres.map(p => { const s = p.querySelector('svg'); return +(s.getBoundingClientRect().width / s.viewBox.baseVal.width).toFixed(2); }),
   overflow: document.documentElement.scrollWidth - innerWidth })
// animated figures: click each step button and read fig.dataset.step; scroll one into view and sample dataset.step every 2.2 s
// lab frame: iframe.style.height set, and inside it scrollHeight - clientHeight is 0
```

Read at least one screenshot per diagram before calling it done.
