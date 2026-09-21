#!/usr/bin/env python3
"""Build the static site from docs/.

The Markdown under docs/ is canonical. This renders it; nothing here is ever
hand-edited, and the output is a build artifact (site/dist/, gitignored).

Three kinds of input:

  RENDERED   a .md with unique content -> one page, shared shell and nav.
  COPIED     a standalone .html that already exists under docs/ -> copied in.
             These are interactive (the drill scores you, the labs move) and
             could not be produced from Markdown.
  SKIPPED    a file deliberately left out, with the reason recorded below and
             printed on every build, so an omission is never silent.

The skip list is the "nothing is repeated" rule, made explicit. Measured
8-word-phrase overlap is in the comment beside each entry.

    pip install -r site/requirements.txt
    python3 site/build.py
    python3 -m http.server -d site/dist 8000
"""
import io
import os
import re
import shutil
import sys

try:
    import markdown
except ImportError:
    sys.exit("markdown is not installed.  pip install -r site/requirements.txt")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DIST = os.path.join(ROOT, "site", "dist")
REPO_URL = "https://github.com/Sourav692/Agent_Evaluation_Demystified/blob/main/"

# --------------------------------------------------------------------------
# What the site is made of
# --------------------------------------------------------------------------

# section -> [(source under docs/, output slug, nav title, one-line blurb)]
RENDER = {
    "Theory": [
        ("concepts/rag-agent-tool-evaluation.md", "field-guide",
         "The field guide",
         "Course 01's companion. The taxonomy, what each check catches and misses, "
         "LLM-as-judge failure modes, and a debugging loop. Tool-agnostic."),
        ("concepts/databricks-mlflow-evals.md", "databricks-mlflow",
         "MLflow &amp; Databricks",
         "Course 02's companion: the agent under test, concepts by theme, "
         "32 gotchas as symptom &rarr; cause &rarr; fix, and the numbers."),
        ("concepts/online_vs_offline_evaluation.md", "online-vs-offline",
         "Online vs. offline",
         "The two regimes side by side, what flows between them, and why a 5% "
         "sample cannot see a two-point regression."),
    ],
    "Audits": [
        ("guide-audits/openai-eval-guide-coverage-gaps.md", "openai-audit",
         "OpenAI guide audit",
         "This repo measured against OpenAI's evaluation guide, per course. "
         "Every topic badged, with the gap list and the corrections."),
        ("guide-audits/genai-eval-playbook-coverage-map.md", "fde-playbook-audit",
         "FDE playbook audit",
         "The same exercise against a customer-facing playbook. All 20 sections "
         "mapped; the gaps cluster in commercial apparatus."),
    ],
    "Interview prep": [
        ("interview-prep/QUESTION_BANK.md", "question-bank",
         "The question bank",
         "35 situational questions, 25 metric questions, 19 long-form cases and "
         "five appendices. The readable reference; the drill is the quiz."),
        ("study-guide/evaluation-roadmap.md", "roadmap",
         "The roadmap",
         "The complete path, basic to expert: ten levels with exit checks, then "
         "what an OpenAI round pushes on and the Databricks track as its own ladder."),
    ],
}

# standalone pages already under docs/ -- interactive, not producible from Markdown
COPY = {
    "Interview prep": [
        ("interview-prep/evaluation-round-drill.html", "The self-quiz drill",
         "The same questions and cases with every answer hidden until you reveal "
         "it. Rate your recall, filter to what is still weak."),
        ("interview-prep/fde-playbook-end-to-end-evaluation.html",
         "End-to-end evaluation",
         "The FDE playbook's sections 1&ndash;14 on one page: the pipeline, then "
         "what happens at each stage."),
        ("interview-prep/stratified-reporting-explained.html",
         "Stratified reporting",
         "Why one overall score is the most dangerous number on a dashboard, "
         "built around a single table."),
        ("study-guide/evaluation-study-plan.html", "The study plan",
         "Seven stages ordered by what the round tests, with time estimates and "
         "a 2&ndash;3 day fast path."),
    ],
    "Audits": [
        ("guide-audits/openai-eval-guide-tutorial.html", "The tutorial",
         "The OpenAI guide in plain language &mdash; 3&ndash;4 lines a concept, "
         "the notebook that teaches it, and 21 TODOs."),
    ],
    "Interactive labs": [
        ("interactive-labs/00-evaluation-index.html", "The surface map",
         "Pipeline, what breaks where, reference-based vs referenceless."),
        ("interactive-labs/01-deterministic-retrieval-metrics.html",
         "Lab 01 &middot; Deterministic retrieval",
         "Drag K: precision moves non-monotonically, recall stalls, MRR never moves."),
        ("interactive-labs/02-llm-judged-retrieval-metrics.html",
         "Lab 02 &middot; Judged retrieval",
         "Reorder three chunks, adding and removing nothing, and precision alone drops."),
        ("interactive-labs/03-generator-metrics.html",
         "Lab 03 &middot; Generator metrics",
         "An answer scoring 1.00 faithfulness and 1.00 relevancy while being flatly false."),
        ("interactive-labs/04-tool-use-evaluation.html",
         "Lab 04 &middot; Tool use",
         "Five broken traces all score 1.00 until you demand exact matching."),
        ("interactive-labs/05-agent-trajectory-evaluation.html",
         "Lab 05 &middot; Trajectory",
         "Five of nine metrics never move; task success reports a clean pass on 40% waste."),
    ],
    "Roadmap explainers": [
        ("roadmap-explainers/00-orientation.html",
         "Level 0 &middot; Orientation",
         "Draw the five-layer taxonomy from memory and choose between a deterministic "
         "scorer and a judge without hesitating."),
        ("roadmap-explainers/01-rag-retrieval-and-generation.html",
         "Level 1 &middot; RAG: retrieval &amp; generation",
         "Separate a retrieval failure from a generation failure with numbers, and know "
         "the one failure no referenceless metric can see."),
        ("roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.html",
         "Level 2 &middot; Agents, tools, trajectories &amp; outcomes",
         "Hold three things apart &mdash; mechanics, process, outcome &mdash; and reach "
         "for the system of record before any judge."),
        ("roadmap-explainers/03-ground-truth.html",
         "Level 3 &middot; Ground truth",
         "Know where cases and labels come from on day one and by month three, and the "
         "two ways a dataset lies to you."),
        ("roadmap-explainers/04-judges-and-the-humans-who-validate-them.html",
         "Level 4 &middot; Judges &amp; the humans who validate them",
         "Build a judge three ways, catch it lying three ways, and know the only thing "
         "that licenses trusting it."),
        ("roadmap-explainers/05-statistics-and-stratified-reporting.html",
         "Level 5 &middot; Statistics &amp; stratified reporting",
         "Refuse to act on a number you cannot resolve, and never report an average "
         "that buries a segment."),
        ("roadmap-explainers/06-the-release-gate-and-ci.html",
         "Level 6 &middot; The release gate &amp; CI",
         "Turn metrics into a decision that can refuse a deploy, and put the cost of "
         "loosening it on a named line."),
        ("roadmap-explainers/07-online-evaluation-and-the-loop.html",
         "Level 7 &middot; Online evaluation &amp; the loop",
         "Measure without an answer key, alert only on what you can resolve, and carry "
         "every finding back into a gated test."),
        ("roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.html",
         "Level 8 &middot; Safety, adversarial &amp; multi-agent attribution",
         "Separate what must never happen from what should usually happen, test by "
         "attack surface, and say which agent broke a multi-agent run."),
        ("roadmap-explainers/09-the-harness-as-a-product.html",
         "Level 9 &middot; The harness as a product",
         "Keep the evaluation system itself trustworthy and affordable &mdash; the "
         "layer above the metrics."),
    ],
}

# Deliberate omissions. Printed on every build so nothing disappears quietly.
SKIP = [
    ("guide-audits/openai-eval-guide-tutorial.md",
     "87.7% identical to its own .html, which ships instead. The repo's rule is "
     "that the Markdown is canonical and the page is not a second source -- so "
     "the site carries one of them, not both."),
    ("README.md", "Folder index. Its job is done by this site's navigation."),
    ("concepts/README.md", "Folder index -- see navigation."),
    ("guide-audits/README.md", "Folder index -- see navigation."),
    ("interactive-labs/README.md", "Folder index -- see navigation."),
    ("interview-prep/README.md",
     "Folder index, and 16.5% the question bank plus 14.4% the drill -- it "
     "summarises pages the site already carries."),
    ("study-guide/README.md", "Folder index -- see navigation."),
]

SECTION_ORDER = ["Theory", "Interview prep", "Audits", "Interactive labs", "Roadmap explainers"]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def slug_for(src):
    for entries in RENDER.values():
        for s, slug, _, _ in entries:
            if s == src:
                return slug + ".html"
    return None


def copied_name(src):
    return os.path.basename(src)


def rewrite_link(href, src_path):
    """Point links at the site's flat layout, or out to GitHub."""
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return href

    anchor = ""
    if "#" in href:
        href, anchor = href.split("#", 1)
        anchor = "#" + anchor
    if not href:
        return anchor

    # resolve relative to the source file, then make it relative to docs/
    abs_target = os.path.normpath(os.path.join(os.path.dirname(src_path), href))
    rel = os.path.relpath(abs_target, "docs") if abs_target.startswith("docs") else None

    if rel:
        page = slug_for(rel)
        if page:
            return page + anchor
        for entries in COPY.values():
            for s, _, _ in entries:
                if s == rel:
                    return copied_name(s) + anchor
        # a docs file the site does not carry (a folder README) -> its section
        if rel.endswith("README.md"):
            return "index.html" + anchor

    # anything else in the repo -- notebooks, modules, the archive
    return REPO_URL + abs_target.replace(os.sep, "/") + anchor


LINK = re.compile(r'(<a [^>]*href=")([^"]+)(")')

# ```mermaid fences render as a plain code block by default. Mermaid reads
# element.textContent, and the browser decodes the entities the Markdown
# renderer escaped (&lt;br/&gt; -> <br/>), so the escaped body can be handed
# over untouched -- only the wrapper changes.
MERMAID = re.compile(r'<pre><code class="language-mermaid">(.*?)</code></pre>', re.S)

# The diagrams in docs/ hard-code light fills (style X fill:#e8f4f8 and similar).
# Mermaid's dark theme draws label text light, which puts light text on those
# light fills and makes subgraph titles unreadable. So the light theme is pinned
# and the figure sits on its own light panel -- the authored colours then work
# in both site themes, and the diagram reads as a figure rather than a hole.
MERMAID_SCRIPT = """
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: true,
    theme: "default",
    themeVariables: { fontFamily: '"Newsreader", Georgia, serif', fontSize: "14px" },
    flowchart: { htmlLabels: true, curve: "basis", useMaxWidth: false },
  });

  // useMaxWidth:false is not enough on its own -- mermaid still pins an inline
  // max-width on some diagrams, which fitted five wide `flowchart LR` pipelines
  // to the column and left them 43-124px tall, unreadable. Size each diagram
  // from its own viewBox instead, so pre.mermaid (overflow-x:auto) scrolls when
  // one is wider than the column. That is the natural gesture for a
  // left-to-right pipeline, and it beats a sliver.
  //
  // Driven by an observer rather than awaiting mermaid.run(): startOnLoad does
  // the rendering, and hooking the promise proved unreliable -- it rejected
  // after having drawn every diagram, which skipped the sizing pass entirely.
  // childList only, so writing the styles cannot retrigger this.
  const sizeFromViewBox = () => {
    for (const svg of document.querySelectorAll("pre.mermaid svg")) {
      const box = svg.viewBox && svg.viewBox.baseVal;
      if (box && box.width > 0 && box.height > 0 && !svg.dataset.aedSized) {
        svg.dataset.aedSized = "1";
        svg.style.maxWidth = "none";
        svg.style.width = box.width + "px";
        svg.style.height = box.height + "px";
      }
    }
  };
  new MutationObserver(sizeFromViewBox)
    .observe(document.body, { subtree: true, childList: true });
  addEventListener("load", () => setTimeout(sizeFromViewBox, 60));
</script>"""


# The question bank is 35,631 words: 35 questions, 19 cases and 25 metric
# questions. Read straight through that is an enormous scroll, and finding one
# question means passing every answer before it. Each question becomes a
# <details>, closed by default, so the page opens as a browsable list and you
# expand only what you want.
#
# Matched on the heading text, not on a hand-kept list, so a question added to
# the Markdown is collapsible without touching this file. The heading stays
# inside the <summary>, which keeps the document outline intact, and its id
# moves to the <details> so existing anchors still resolve.
HEADING = re.compile(r"<h([1-6])([^>]*)>(.*?)</h\1>", re.S)
QA_HEAD = re.compile(r"^(Q\d+|Case\s+\d+)\s*[\u2014\u2013-]\s*(.*)$", re.S)
HEAD_ID = re.compile(r'id="([^"]+)"')


# Closed <details> is invisible to find-in-page in some browsers, and a reader
# arriving from an anchor should not land on a shut drawer. Both are handled
# here rather than asking the reader to work around them.
QA_SCRIPT = """
<script>
(function () {
  var all = document.querySelectorAll("details.qa");
  if (!all.length) return;

  var bar = document.createElement("div");
  bar.className = "qa-bar";
  bar.innerHTML = '<span class="qa-count">' + all.length + ' questions</span>' +
    '<button type="button" data-qa="open">Expand all</button>' +
    '<button type="button" data-qa="shut">Collapse all</button>';
  var doc = document.querySelector("article.doc");
  var first = all[0];
  first.parentNode.insertBefore(bar, first);

  bar.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-qa]");
    if (!b) return;
    var open = b.dataset.qa === "open";
    for (var i = 0; i < all.length; i++) { all[i].open = open; }
  });

  // An anchor should open what it points at, and actually land on it.
  //
  // Landing is the hard half. Mermaid swaps 40 lines of source text for a
  // 1404px and an 1818px SVG, and the webfonts reflow everything, so the
  // target's document position moves by thousands of pixels after this script
  // first runs -- aiming once left the reader 3,000px past the question. So
  // re-aim every frame until the target stops moving, then stop. Bounded at
  // ~2s, and abandoned the instant the reader scrolls for themselves.
  // Chrome restores the previous scroll offset for this URL *after* this
  // script runs, which silently overrode the aim and parked the reader ~3,000px
  // past the question on every repeat visit. With a hash present the anchor is
  // the intent, not the old offset.
  if (location.hash && "scrollRestoration" in history) {
    history.scrollRestoration = "manual";
  }

  var userMoved = false;
  ["wheel", "touchstart", "keydown"].forEach(function (t) {
    addEventListener(t, function () { userMoved = true; }, { passive: true, once: true });
  });

  function aim() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) { return; }
    var el = document.getElementById(id);
    if (!el) { return; }
    for (var n = el; n; n = n.parentElement) {
      if (n.tagName === "DETAILS") { n.open = true; }
    }
    // behavior:"instant" matters -- the site sets scroll-behavior:smooth, so
    // plain scrollTo starts an animation that the next frame restarts. The
    // loop then "converged" on a scroll still in flight and left the reader
    // ~3,000px short. Converge on where the target actually sits instead.
    // clear the sticky top bar, or the question row lands behind it
    var bar = document.querySelector(".bar");
    var gap = (bar ? bar.offsetHeight : 0) + 14;
    var still = 0, frames = 0;
    (function settle() {
      if (userMoved || frames++ > 150) { return; }
      var top = el.getBoundingClientRect().top;
      if (Math.abs(top - gap) > 2) {
        still = 0;
        window.scrollTo({ top: Math.max(0, top + window.scrollY - gap), behavior: "instant" });
      } else {
        still++;
      }
      if (still < 4) { requestAnimationFrame(settle); }
    })();
  }
  addEventListener("hashchange", function () { userMoved = false; aim(); });
  aim();

  // print the whole thing, never a page of shut drawers
  addEventListener("beforeprint", function () {
    for (var i = 0; i < all.length; i++) { all[i].open = true; }
  });
})();
</script>"""


def collapsify(html):
    """Wrap each question and case in <details>. Returns (html, count)."""
    heads = list(HEADING.finditer(html))
    jobs = []
    for i, m in enumerate(heads):
        level = int(m.group(1))
        label = QA_HEAD.match(re.sub(r"<[^>]+>", "", m.group(3)).strip())
        if not label:
            continue
        # the section runs to the next heading at this level or shallower
        end = len(html)
        for nxt in heads[i + 1:]:
            if int(nxt.group(1)) <= level:
                end = nxt.start()
                break
        ident = HEAD_ID.search(m.group(2) or "")
        jobs.append((m.start(), m.end(), end, level, m.group(3),
                     label.group(1), label.group(2).strip(),
                     ident.group(1) if ident else ""))

    # splice from the end so earlier offsets stay valid
    for start, head_end, end, level, inner, num, rest, ident in reversed(jobs):
        body = html[head_end:end]
        html = html[:start] + (
            '<details class="qa"%s>'
            '<summary><h%d class="qa-h">'
            '<span class="qa-n">%s</span><span class="qa-q">%s</span>'
            '</h%d></summary>'
            '<div class="qa-body">%s</div>'
            '</details>'
        ) % (' id="%s"' % ident if ident else "", level, num, rest, level, body) + html[end:]
    return html, len(jobs)


# The "In plain English" blocks are the long, slow walk-through of an answer --
# valuable when you want it, noise when you are scanning. Each one runs from its
# own label to whichever section starts next, so the end marker has to be an
# explicit list: the first bold inside a block is inline emphasis, not a new
# section. Verified against all 20 blocks in the bank.
PLAIN_START = '<p><strong>In plain English:</strong></p>'
#
# <h1> belongs in this list as much as <h2>: the last case in a Tier is
# followed by the next Tier's <h1> and nothing else, so leaving h1 out let the
# drawer swallow nine section headings -- invisible on the page, and fatal to
# anything that navigates by heading.
PLAIN_END = re.compile(
    r'<p><strong>(?:The trap|Weak answer|Killer follow-ups|If they push|'
    r'What good looks like|Scoring|Follow-ups)\b|<h[1-4][ >]')


def plainify(html):
    """Collapse each 'In plain English' block. Returns (html, count)."""
    out, at, n = [], 0, 0
    while True:
        i = html.find(PLAIN_START, at)
        if i < 0:
            out.append(html[at:])
            break
        body_start = i + len(PLAIN_START)
        m = PLAIN_END.search(html, body_start)
        end = m.start() if m else len(html)
        out.append(html[at:i])
        out.append('<details class="plain"><summary>In plain English</summary>'
                   '<div class="plain-body">%s</div></details>' % html[body_start:end])
        at = end
        n += 1
    return "".join(out), n


def mermaidise(html):
    """Turn mermaid code blocks into diagram containers. Returns (html, count)."""
    count = len(MERMAID.findall(html))
    if count:
        html = MERMAID.sub(lambda m: '<pre class="mermaid">%s</pre>' % m.group(1), html)
    return html, count


# ---- in-document section rail -------------------------------------------
#
# Long documents here are one flat Markdown file with 25 top-level sections,
# so the only way to reach Tier F is to scroll past everything before it. The
# rail is built from the <h1> ids the `toc` extension already assigns -- no
# new source markup, and it cannot drift from the headings.
#
# Only pages with enough sections to be worth navigating get one; below the
# threshold a rail is just a second, worse table of contents.
DOCNAV_MIN = 4

# Appendices are reference material read by search, not a leg of the journey
# through the document, so they are left off the rail by request.
DOCNAV_SKIP = ("appendix",)

H1 = re.compile(r'<h1 id="([^"]+)"[^>]*>(.*?)</h1>', re.S)
FAMILY = [
    (re.compile(r"^Part\s+(\d+)\s*[\u2014\u2013-]\s*(.*)$", re.S), "part"),
    (re.compile(r"^Tier\s+([A-Z])\s*[\u2014\u2013-]\s*(.*)$", re.S), "tier"),
    (re.compile(r"^Appendix\s+([A-Z])\s*[\u2014\u2013-]\s*(.*)$", re.S), "appendix"),
]


def docnav(html):
    """Build the sticky section rail from the page's <h1>s. Returns (html, n).

    The first heading is the document title, which is not a section -- it
    becomes the rail's way back to the top, labelled Orientation to match the
    drill.
    """
    heads = H1.findall(html)
    if len(heads) < DOCNAV_MIN:
        return "", 0

    items, prev = [], None
    for n, (hid, raw) in enumerate(heads):
        text = re.sub(r"<[^>]+>", "", raw).strip()
        if n == 0:
            items.append(("", "\u2014", "Orientation", hid))
            continue
        for pat, fam in FAMILY:
            m = pat.match(text)
            if m:
                idx = m.group(1)
                items.append((fam, idx.zfill(2) if fam == "part" else idx,
                              m.group(2).strip(), hid))
                break
        else:
            # A section that follows none of the three naming schemes still
            # belongs in the rail; it just has no index to show.
            items.append(("other", "\u00b7", text, hid))

    items = [it for it in items if it[0] not in DOCNAV_SKIP]

    # Families are captioned rather than merely ruled off: Tier A..H indexes by
    # bare letter, and a lone column of letters names nothing.
    caption = {"part": "Parts", "tier": "Tiers", "other": "Sections", "": ""}
    out = ['<nav class="docnav" aria-label="Sections">']
    for fam, idx, label, hid in items:
        if fam != prev:
            if prev is not None:
                out.append("</ol>")
            if caption.get(fam):
                out.append('<p class="famhead">%s</p>' % caption[fam])
            out.append("<ol>")
        prev = fam
        out.append('<li><a href="#%s"><span class="i">%s</span>'
                   '<span class="t">%s</span></a></li>' % (hid, idx, label))
    out.append("</ol></nav>")
    return "".join(out), len(items)


# Which rail item is current is a scroll question, not a structural one, so it
# is answered in the browser. `scrollIntoView` is deliberately not used for the
# rail's own scrolling -- the page sets scroll-behavior:smooth, and a smooth
# animation started here fights the one the anchor click already began.
DOCNAV_SCRIPT = """
<script>
(function () {
  var rail = document.querySelector(".docnav");
  if (!rail) return;
  var links = [].slice.call(rail.querySelectorAll("a"));
  var heads = links.map(function (a) {
    return document.getElementById(decodeURIComponent(a.hash.slice(1)));
  });

  var current = -1;
  function mark() {
    var line = 90, at = 0;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i] && heads[i].getBoundingClientRect().top <= line) { at = i; }
    }
    if (at === current) return;
    if (current >= 0) { links[current].classList.remove("on"); }
    links[at].classList.add("on");
    current = at;

    // Keep the active item visible when the rail is taller than the viewport.
    var r = links[at].getBoundingClientRect(), box = rail.getBoundingClientRect();
    if (r.top < box.top + 8) { rail.scrollTop -= box.top + 8 - r.top; }
    else if (r.bottom > box.bottom - 8) { rail.scrollTop += r.bottom - box.bottom + 8; }
  }

  var queued = false;
  function onScroll() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; mark(); });
  }
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll, { passive: true });

  // Scrolling is not the only thing that moves a heading past the line. Web
  // fonts reflow the whole document, mermaid replaces source text with a tall
  // SVG, and expanding a question pushes every later section down -- none of
  // which fire `scroll`. Watching the article's box catches all three, and it
  // is the difference between a rail that is right and one that is right until
  // the reader touches something.
  var doc = document.querySelector("article.doc");
  if (doc && window.ResizeObserver) { new ResizeObserver(onScroll).observe(doc); }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(mark); }
  mark();
})();
</script>
"""


# A back-link bar for the copied pages, which arrive with their own complete
# stylesheet and no site chrome. Three of them (the drill, the study plan, the
# tutorial) already have a sticky header of their own, and the labs do not
# define --surface/--rule at all -- so this is deliberately NOT sticky and uses
# no CSS variables. Everything is literal, scoped to .aed-sitebar, and carries
# its own light/dark rules, so it cannot collide with or depend on the page.
SITEBAR = """<style>
.aed-sitebar{display:flex;align-items:baseline;gap:24px;flex-wrap:wrap;
  padding:13px 20px;border-bottom:1px solid #C5C8C2;background:#E4E6E1;
  font-family:"Spline Sans Mono",ui-monospace,Menlo,monospace;
  font-size:12.5px;line-height:1.4}
.aed-sitebar a{color:#3C4E51;text-decoration:none;white-space:nowrap}
.aed-sitebar a:hover{color:#0E2226}
.aed-sitebar .aed-brand{font-family:"Newsreader",Georgia,serif;font-size:18px;
  font-weight:600;letter-spacing:-.012em;color:#0E2226}
.aed-sitebar .aed-links{display:flex;gap:20px;flex-wrap:wrap;color:#3C4E51}
@media (prefers-color-scheme:dark){
  .aed-sitebar{background:#0D1618;border-bottom-color:#26383B}
  .aed-sitebar a{color:#9FB1B1}
  .aed-sitebar a:hover{color:#DDE5E3}
  .aed-sitebar .aed-brand{color:#DDE5E3}
  .aed-sitebar .aed-links{color:#9FB1B1}
}
@media print{.aed-sitebar{display:none}}
</style>
<div class="aed-sitebar">
  <a class="aed-brand" href="index.html">&larr; Agent Evaluation Demystified</a>
  <span class="aed-links">%s</span>
</div>"""


def sitebar():
    links = "".join('<a href="index.html#%s">%s</a>'
                    % (s.lower().replace(" ", "-"), s) for s in SECTION_ORDER)
    return SITEBAR % links


BODY_OPEN = re.compile(r"(<body[^>]*>)", re.I)


def badge_for(html_path):
    """A copied page is only 'interactive' if it actually does something.

    Two of these pages are hand-written but static, so the bucket a file sits
    in does not tell you how it behaves -- the file does.
    """
    text = io.open(html_path, encoding="utf-8").read()
    handlers = sum(text.count(t) for t in
                   ("addEventListener", "onclick", "oninput", "onchange", "localStorage"))
    if handlers:
        return "interactive"
    prose = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.S)
    return "{:,} words".format(len(re.sub(r"<[^>]+>", " ", prose).split()))


def shell(title, body, nav, blurb="", is_index=False, diagrams=0, qa=0, rail=0):
    home = "" if is_index else '<a class="home" href="index.html">&larr; All documents</a>'
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Spline+Sans+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="bar">
  <a class="brand" href="index.html">Agent Evaluation <span>Demystified</span></a>
  <nav>%s</nav>
</header>
<main class="wrap">
%s
%s
</main>
<footer class="foot">
  <p>Generated from the Markdown in <code>docs/</code> by <code>site/build.py</code>.
  The Markdown is canonical &mdash; edit there and rebuild.</p>
</footer>%s
</body>
</html>
""" % (title, blurb, nav, home, body,
       (MERMAID_SCRIPT if diagrams else "") + (QA_SCRIPT if qa else "")
       + (DOCNAV_SCRIPT if rail else ""))


def top_nav(active_section):
    out = []
    for s in SECTION_ORDER:
        cls = ' class="on"' if s == active_section else ""
        out.append('<a%s href="index.html#%s">%s</a>' % (cls, s.lower().replace(" ", "-"), s))
    return "".join(out)


def build():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "assets"))

    shutil.copy(os.path.join(ROOT, "site", "site.css"),
                os.path.join(DIST, "assets", "site.css"))

    rendered, copied = [], []

    for section in SECTION_ORDER:
        for src, slug, title, blurb in RENDER.get(section, []):
            path = os.path.join(DOCS, src)
            text = io.open(path, encoding="utf-8").read()
            md = markdown.Markdown(extensions=["tables", "fenced_code", "toc",
                                               "sane_lists", "attr_list"])
            html = md.convert(text)
            html = LINK.sub(
                lambda m: m.group(1) + rewrite_link(m.group(2), "docs/" + src) + m.group(3),
                html)
            html, diagrams = mermaidise(html)
            html, plains = plainify(html)
            html, questions = collapsify(html)
            rail, sections = docnav(html)
            article = '<article class="doc">%s</article>' % html
            body = '<div class="withnav">%s%s</div>' % (rail, article) if rail else article
            page = shell(re.sub("<[^>]+>", "", title), body,
                         top_nav(section), re.sub("<[^>]+>", "", blurb),
                         diagrams=diagrams, qa=questions, rail=sections)
            io.open(os.path.join(DIST, slug + ".html"), "w", encoding="utf-8").write(page)
            rendered.append((src, slug + ".html", len(text.split()), diagrams,
                             questions, plains, sections))

        for src, title, blurb in COPY.get(section, []):
            # Copied pages carry links written for their old home under docs/ --
            # a .md target, or a folder-relative path. Rewrite them the same way
            # as rendered pages so the flat site has no dead links.
            text = io.open(os.path.join(DOCS, src), encoding="utf-8").read()
            text = LINK.sub(
                lambda m: m.group(1) + rewrite_link(m.group(2), "docs/" + src) + m.group(3),
                text)
            text, n = BODY_OPEN.subn(lambda m: m.group(1) + "\n" + sitebar(), text, count=1)
            if not n:
                raise SystemExit("no <body> to attach the nav bar to: %s" % src)
            io.open(os.path.join(DIST, copied_name(src)), "w", encoding="utf-8").write(text)
            copied.append((src, copied_name(src)))

    # ---- index
    cards = []
    for section in SECTION_ORDER:
        items = []
        for src, slug, title, blurb in RENDER.get(section, []):
            words = len(io.open(os.path.join(DOCS, src), encoding="utf-8").read().split())
            items.append('<li><a href="%s.html">%s</a><span class="meta">%s words</span>'
                         '<p>%s</p></li>' % (slug, title, "{:,}".format(words), blurb))
        for src, title, blurb in COPY.get(section, []):
            items.append('<li><a href="%s">%s</a><span class="meta">%s</span>'
                         '<p>%s</p></li>'
                         % (copied_name(src), title,
                            badge_for(os.path.join(DIST, copied_name(src))), blurb))
        if items:
            cards.append('<section id="%s"><h2>%s</h2><ul class="cards">%s</ul></section>'
                         % (section.lower().replace(" ", "-"), section, "".join(items)))

    skips = "".join('<tr><td><code>docs/%s</code></td><td>%s</td></tr>' % (s, why)
                    for s, why in SKIP)
    body = """<h1>Agent Evaluation Demystified</h1>
<p class="lede">How do you know your RAG system or agent is actually working? These are the
written companions &mdash; the theory, the audits, the interview material and the
interactive labs. The notebooks live in
<a href="%(repo)scourses/">the repository</a>.</p>
%(cards)s
<section id="not-here">
<h2>What is deliberately not here</h2>
<p>Every page on this site is the only place its content appears. These files under
<code>docs/</code> were left out on purpose:</p>
<table class="skips"><thead><tr><th>File</th><th>Why</th></tr></thead><tbody>%(skips)s</tbody></table>
</section>""" % {"repo": REPO_URL, "cards": "".join(cards), "skips": skips}

    io.open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(
        shell("Agent Evaluation Demystified", body, top_nav(None),
              "Written companions to a hands-on course in evaluating RAG systems and agents.",
              is_index=True))

    # ---- report
    print("rendered from Markdown:")
    for src, out, w, d, q, pl, sec in rendered:
        extra = "  ".join(x for x in (("%d diagrams" % d) if d else "",
                                      ("%d collapsible" % q) if q else "",
                                      ("%d plain-English" % pl) if pl else "",
                                      ("%d-item rail" % sec) if sec else "") if x)
        print("   %-48s -> %-26s %6s words  %s"
              % (src, out, "{:,}".format(w), extra))
    print("\ncopied as-is (interactive, not producible from Markdown):")
    for src, out in copied:
        print("   %-48s -> %s" % (src, out))
    print("\nskipped on purpose:")
    for src, why in SKIP:
        print("   %-48s %s" % (src, why[:60] + ("..." if len(why) > 60 else "")))
    print("\n%d pages in site/dist/  (%d rendered, %d copied, 1 index)"
          % (len(rendered) + len(copied) + 1, len(rendered), len(copied)))


if __name__ == "__main__":
    build()
