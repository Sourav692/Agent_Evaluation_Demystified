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
import glob
import io
import json
import os
import re
import shutil
import sys
from html import escape
from xml.sax.saxutils import escape as xml_escape

from head import SITE_URL, footer, head_tags, page_url

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
        ("concepts/customer-support-multi-agent-case-study.md", "support-case-study",
         "Support-system case study",
         "One multi-tenant support agent evaluated end to end: every stage's checks, "
         "the offline suite, the release gate, the canary and online signals."),
        ("concepts/cost-tracking-and-guardrails.md", "cost-and-guardrails",
         "Cost and guardrails",
         "The same system's cost: per-request, per-agent and per-tenant attribution, "
         "budgets, and five guardrail boundaries &mdash; and how cost gates a release."),
    ],
    "Audits": [
        ("guide-audits/openai-eval-guide-coverage-gaps.md", "openai-audit",
         "OpenAI guide audit",
         "This repo measured against OpenAI's evaluation guide, per course. "
         "Every topic badged, with the gap list and the corrections."),
        ("guide-audits/openai-eval-guide-tutorial.md", "openai-eval-guide-tutorial",
         "The tutorial",
         "The OpenAI guide in plain language &mdash; 3&ndash;4 lines a concept, "
         "the notebook that teaches it, and 21 TODOs."),
    ],
    "Interview prep": [
        ("interview-prep/QUESTION_BANK.md", "question-bank",
         "The question bank",
         "35 situational questions, 30 metric questions, 19 long-form cases and "
         "seven appendices. The readable reference; the drill is the quiz."),
        ("study-guide/evaluation-roadmap.md", "roadmap",
         "The roadmap",
         "The complete path, basic to expert: ten levels with exit checks, then "
         "what an OpenAI round pushes on and the Databricks track as its own ladder."),
        ("study-guide/evaluation-topic-notebook-mapping.md", "topic-notebook-mapping",
         "Topic &amp; notebook mapping",
         "The roadmap's resource index: for every level, which notebook, explainer, "
         "lab or question teaches each topic, and what running it costs."),
        ("study-guide/evaluation-templates.md", "evaluation-templates",
         "Evaluation templates",
         "Four fill-in documents: a scorecard, a failure-investigation report, an "
         "acceptance-criteria document and a regression report."),
    ],
    "Roadmap explainers": [
        ("roadmap-explainers/00-orientation.md", "00-orientation",
         "Level 0 &middot; Orientation",
         "Decompose the system before measuring it, because one quality score cannot say which stage broke."),
        ("roadmap-explainers/01-rag-retrieval-and-generation.md", "01-rag-retrieval-and-generation",
         "Level 1 &middot; RAG: retrieval &amp; generation",
         "Evaluate retrieval and generation as two separate systems, because a generator cannot be judged on evidence it never received."),
        ("roadmap-explainers/02-agents-tools-conversations-trajectories-outcomes.md", "02-agents-tools-conversations-trajectories-outcomes",
         "Level 2 &middot; Agents, tools, trajectories &amp; outcomes",
         "Score mechanics, process and outcome separately, because passing any one of the three says nothing about the other two."),
        ("roadmap-explainers/03-ground-truth.md", "03-ground-truth",
         "Level 3 &middot; Ground truth",
         "Collect inputs from real traffic but never labels from the system under test, because a dataset built from its own answers can only agree with itself."),
        ("roadmap-explainers/04-judges-and-the-humans-who-validate-them.md", "04-judges-and-the-humans-who-validate-them",
         "Level 4 &middot; Judges &amp; the humans who validate them",
         "A judge is the only way to score open-ended text at scale, and it cannot be trusted until it is measured against the people who do not scale."),
        ("roadmap-explainers/05-statistics-and-stratified-reporting.md", "05-statistics-and-stratified-reporting",
         "Level 5 &middot; Statistics &amp; stratified reporting",
         "Gate on the worst slice rather than the average, because a group is only as loud in the mean as it is big."),
        ("roadmap-explainers/06-the-release-gate-and-ci.md", "06-the-release-gate-and-ci",
         "Level 6 &middot; The release gate &amp; CI",
         "Gate against what is live, not against a fixed bar, because a system can lose seven points without any single release ever failing."),
        ("roadmap-explainers/07-online-evaluation-and-the-loop.md", "07-online-evaluation-and-the-loop",
         "Level 7 &middot; Online evaluation &amp; the loop",
         "Every check that needs an answer key dies at deployment, and it dies silently &mdash; reporting &quot;skipped&quot; rather than failing."),
        ("roadmap-explainers/08-safety-adversarial-and-multi-agent-attribution.md", "08-safety-adversarial-and-multi-agent-attribution",
         "Level 8 &middot; Safety, adversarial &amp; multi-agent attribution",
         "Report safety as a list of case IDs rather than a percentage, because a percentage cannot be opened and read."),
        ("roadmap-explainers/09-the-harness-as-a-product.md", "09-the-harness-as-a-product",
         "Level 9 &middot; The harness as a product",
         "A harness that only computes numbers is not yet a product, because nobody has agreed what the numbers must reach or who signs off on them."),
        ("roadmap-explainers/10-the-enterprise-harness-end-to-end.md", "10-the-enterprise-harness-end-to-end",
         "Level 10 &middot; The whole harness, end to end",
         "Every stage produces the artifact the next one consumes, so a skipped stage does not fail &mdash; it keeps reporting green while measuring nothing."),
    ],
}

# standalone pages already under docs/ -- interactive, not producible from Markdown
COPY = {
    "Interview prep": [
        ("interview-prep/evaluation-round-drill.html", "The self-quiz drill",
         "The same questions and cases with every answer hidden until you reveal "
         "it. Rate your recall, filter to what is still weak."),
        ("study-guide/evaluation-study-plan.html", "The study plan",
         "Seven stages ordered by what the round tests, with time estimates and "
         "a 2&ndash;3 day fast path."),
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
}

# Deliberate omissions. Printed on every build so nothing disappears quietly.
SKIP = [
    ("README.md", "Folder index. Its job is done by this site's navigation."),
    ("concepts/README.md", "Folder index -- see navigation."),
    ("guide-audits/README.md", "Folder index -- see navigation."),
    ("interactive-labs/README.md", "Folder index -- see navigation."),
    ("interview-prep/README.md",
     "Folder index, and 16.5% the question bank plus 14.4% the drill -- it "
     "summarises pages the site already carries."),
    ("study-guide/README.md", "Folder index -- see navigation."),
]

# Pages about the site rather than the subject. Rendered like RENDER, linked from the
# footer, never carded on the index.
SITE_PAGES = [
    ("about.md", "about", "About", "Who maintains this site, how to report a problem, "
     "how it is built, and the licences."),
    ("CHANGELOG.md", "changelog", "Changelog", "What changed on the site, newest first."),
]

SECTION_ORDER = ["Theory", "Interview prep", "Audits", "Interactive labs", "Roadmap explainers"]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Roadmap topics on the explainer cards
# --------------------------------------------------------------------------
#
# Each explainer card lists what its level actually covers, and the list is
# parsed out of the roadmap at build time rather than retyped here. The roadmap
# is where a level's topics are decided; a second hand-kept copy in this file
# would drift the first time somebody edited one and not the other, which is the
# exact failure check_drill_sync.py exists to catch elsewhere in this repo.
#
# Shape relied on, from docs/study-guide/evaluation-roadmap.md:
#
#     ### Level 3: Ground truth
#     **Topics**
#     - Golden-set case anatomy (six expectations per case)
#     - ...
ROADMAP = os.path.join(DOCS, "study-guide", "evaluation-roadmap.md")
LEVEL_HEAD = re.compile(r"^###\s+Level\s+(\d+):", re.M)

# Level 10 has no roadmap row on purpose -- it is a synthesis of the ten levels,
# not an eleventh level of material -- so its topics are the six stages of its
# own loop, kept here and nowhere else.
EXTRA_TOPICS = {
    10: ["The contract: deciding \u201cgood\u201d before the code exists",
         "Ground truth: the frozen set and the mined set",
         "Offline evaluation across all five layers",
         "The release gate, its four checks, and the CI split",
         "Production and online evaluation with no answer key",
         "Human feedback, judge alignment, and closing the loop",
         "The traps at every stage, and the order to build them in"],
}


def roadmap_topics():
    """{level number: [topic, ...]} parsed from the roadmap's own Topics lists."""
    text = io.open(ROADMAP, encoding="utf-8").read()
    heads = list(LEVEL_HEAD.finditer(text))
    out = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.start():end]
        if "**Topics**" not in body:
            raise SystemExit("roadmap Level %s has no **Topics** list" % m.group(1))
        after = body.split("**Topics**", 1)[1]
        topics = []
        for line in after.splitlines():
            line = line.strip()
            if line.startswith("- "):
                topics.append(line[2:].strip())
            elif topics and line:
                break          # the list ended -- **Goal.** and the rest follow
        if not topics:
            raise SystemExit("roadmap Level %s has an empty Topics list" % m.group(1))
        out[int(m.group(1))] = topics
    out.update(EXTRA_TOPICS)
    return out


def topics_html(slug, topics):
    """The topic list for one explainer card, keyed off its NN- filename prefix.

    Anything in the explainers section has to resolve, so a new level without a
    roadmap entry fails the build instead of quietly rendering a card with no
    topics on it -- indistinguishable, from outside, from a level that has none.
    """
    level = int(slug[:2])
    if level not in topics:
        raise SystemExit("no roadmap topics for explainer level %d (%s)" % (level, slug))
    return ('<ul class="topics">%s</ul>'
            % "".join("<li>%s</li>" % escape(x) for x in topics[level]))


def slug_for(src):
    for entries in [*RENDER.values(), SITE_PAGES]:
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

# References name repo files as `courses/.../08_building_custom_judges.ipynb`
# code spans, which render as dead text on the site. A span that is exactly a
# repo path becomes a link to wherever rewrite_link() sends it: the site page
# for a doc the site serves, GitHub for everything else. Spans inside <pre>,
# an existing <a> or a <script> (the drill builds HTML in JS strings, where an
# inserted href's quotes would break the string) are left alone. Shorthands
# (`courses/01-…/08_x.ipynb`, `courses/02`) link when they match one path.
CODE_PATH = re.compile(
    r"<code>((?:docs|courses|labs|archive|site|\.github)/[^<\s]*)</code>")
SKIP_ZONES = re.compile(r"(<pre\b.*?</pre>|<a\b.*?</a>|<script\b.*?</script>)", re.S)


def linkify_code_paths(html):
    """Wrap repo-path code spans in links. Returns (html, count)."""
    count = 0

    def link(m):
        nonlocal count
        path = m.group(1)
        if "*" in path:  # a glob (`docs/interactive-labs/*.html`) links its folder
            path = path[:path.index("*")].rsplit("/", 1)[0] + "/"
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            hits = glob.glob(os.path.join(ROOT, path.replace("\u2026", "*").rstrip("/") + "*"))
            if len(hits) == 1:
                full = hits[0]
                path = os.path.relpath(full, ROOT) + ("/" if os.path.isdir(full) else "")
        if os.path.isdir(full):
            href = REPO_URL.replace("/blob/", "/tree/") + path.rstrip("/")
        elif os.path.isfile(full):
            href = rewrite_link(path, "x")  # "x" sits at the root: path resolves as written
        else:
            print("   warning: code span names a missing path: %s" % path)
            return m.group(0)
        count += 1
        return '<a href="%s">%s</a>' % (href, m.group(0))

    parts = SKIP_ZONES.split(html)
    for i in range(0, len(parts), 2):  # odd indexes are the skipped zones
        parts[i] = CODE_PATH.sub(link, parts[i])
    return "".join(parts), count


# Once a repo path links a page the site serves, the path itself is a build
# internal: "Docs: docs/concepts/databricks-mlflow-evals.md" reads better as
# "Docs: MLflow & Databricks". The page's nav title replaces the path -- a docs/
# path or a bare file name (`databricks-mlflow-evals.md`, Part 5); text after
# the code span stays. Paths to files the site doesn't serve stay as written.
SITE_LINK = re.compile(
    r'(<a href="([^"#]+\.html)(?:#[^"]*)?">)<code>(?:docs/[^<]*|[^<\s/]+\.md)</code>([^<]*</a>)')


def titlify_site_links(html):
    titles = {slug + ".html": t for s in [*RENDER.values(), SITE_PAGES] for _, slug, t, _ in s}
    titles.update({copied_name(src): t for s in COPY.values() for src, t, _ in s})
    parts = re.split(r"(<script\b.*?</script>)", html, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = SITE_LINK.sub(
            lambda m: m.group(1) + titles[m.group(2)] + m.group(3) if m.group(2) in titles
            else m.group(0), parts[i])
    return "".join(parts)


# Two concept docs were converted by Pandoc and keep its conventions: `\$` (so
# GitHub doesn't read `$2,900 ... $0.029` as maths -- the escape must stay in
# the source), `---` for an em dash (spaced or not) and `1--5` for an en dash. Python-Markdown
# knows none of them and prints them literally. Outside <pre>, <code> and
# <script> they become what Pandoc would have printed.
PANDOC_SKIP = re.compile(r"(<pre\b.*?</pre>|<code\b.*?</code>|<script\b.*?</script>)", re.S)


def pandoc_typography(html):
    parts = PANDOC_SKIP.split(html)
    for i in range(0, len(parts), 2):  # odd indexes are the skipped zones
        t = re.sub(r"(\s|\w)---(\s|\w)", "\\1\u2014\\2", parts[i].replace("\\$", "$"))
        parts[i] = re.sub(r"(\d)--(\d)", "\\1\u2013\\2", t)
    return "".join(parts)

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
  // Mermaid is ~250 KB over ~27 requests. Imported up front, it competed with
  // the page itself for the first paint (question bank LCP 4.6 s on mobile).
  // It loads when the first diagram comes within a screen or two of view, and
  // each diagram renders as it approaches. A diagram in a closed <details>
  // renders when the reader opens it.
  let ready;
  const load = () => ready ||= import(
    "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.esm.min.mjs"
  ).then(({ default: mermaid }) => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "default",
      themeVariables: { fontFamily: '"Newsreader", Georgia, serif', fontSize: "14px" },
      flowchart: { htmlLabels: true, curve: "basis", useMaxWidth: false },
    });
    return mermaid;
  });
  // One run at a time: overlapping mermaid.run() calls drop diagrams (6 of 66
  // when a reader scrolls fast).
  let queue = Promise.resolve();
  const near = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      near.unobserve(e.target);
      queue = queue.then(() => load()).then((m) => m.run({ nodes: [e.target] })).catch(() => {});
    }
  }, { rootMargin: "1200px 0px" });
  document.querySelectorAll("pre.mermaid").forEach((el) => near.observe(el));

  // useMaxWidth:false is not enough on its own -- mermaid still pins an inline
  // max-width on some diagrams, which fitted five wide `flowchart LR` pipelines
  // to the column and left them 43-124px tall, unreadable. Size each diagram
  // from its own viewBox instead, so pre.mermaid (overflow-x:auto) scrolls when
  // one is wider than the column. That is the natural gesture for a
  // left-to-right pipeline, and it beats a sliver.
  //
  // Driven by an observer rather than awaiting mermaid.run(): hooking the
  // promise proved unreliable -- it rejected after having drawn every diagram,
  // which skipped the sizing pass entirely.
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


# The question bank is 35,631 words: 35 questions, 19 cases and 30 metric
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


# Check Yourself ends every explainer with a numbered list: the question, then
# its answer as one trailing **bold** span. Shown inline, the answer is read
# before the question is tried, so it folds behind "Show answer". Only that
# section and only a <strong> that closes its <li> are touched.
CHECK_SECTION = re.compile(r'(<h2 id="check-yourself">.*?)(?=<h2\b|\Z)', re.S)
TRAILING_ANSWER = re.compile(r"(<li>(?:(?!</li>).)*?)(<strong>(?:(?!<strong>).)*?</strong>)(\s*(?:</p>\s*)?</li>)", re.S)


def hide_answers(html):
    """Fold each Check Yourself answer into <details>. Returns (html, count)."""
    count = 0

    def fold(m):
        nonlocal count
        count += 1
        return ('%s<details class="answer"><summary>Show answer</summary>'
                '<div class="answer-body">%s</div></details>%s' % m.groups())

    html = CHECK_SECTION.sub(lambda s: TRAILING_ANSWER.sub(fold, s.group(1)), html)
    return html, count


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


# ---- reusable content components ----------------------------------------
#
# The explainers are prose with three recurring shapes -- a reference table, an
# aside, and a "Notebook: x / Lab: y" credit line under a section heading. Each
# gets one component here rather than a style choice per instance, so a change
# to how asides look is a change in one place. All three are derived from the
# Markdown's own output; none of them needs new source markup.

TABLE = re.compile(r"(<table>.*?</table>)", re.S)

# "*Notebook: `x.ipynb` \u00b7 Lab: `y.html`*" directly under a section heading.
BADGES = re.compile(
    r"<p><em>((?:Notebook|Notebooks|Lab|Source)s?:.*?)</em></p>", re.S)

# A blockquote whose lead-in names a trap reads as a warning; the rest are notes.
WARN = re.compile(r"trap|gotcha|collision|backwards|never|danger|careful|"
                  r"worth flagging|watch out", re.I)


EXAMPLE_H = re.compile(r'<h3 id="[^"]*"[^>]*>(?:(?!</h3>).)*?'
                       r'(?:worked example|walkthrough|worked through)'
                       r'(?:(?!</h3>).)*?</h3>', re.I | re.S)
NEXT_H = re.compile(r"<h[123][ >]")


def worked_examples(html):
    """Tint the worked-example sections so they read as demonstrations.

    The block runs from its own <h3> to whatever heading comes next, which is
    how the Markdown already delimits it -- there is no wrapper in the source
    to key off, and adding one would put presentation into the prose.
    """
    out, at, n = [], 0, 0
    while True:
        m = EXAMPLE_H.search(html, at)
        if not m:
            out.append(html[at:])
            break
        nxt = NEXT_H.search(html, m.end())
        end = nxt.start() if nxt else len(html)
        out.append(html[at:m.start()])
        out.append('<section class="worked-example">%s</section>' % html[m.start():end])
        at = end
        n += 1
    return "".join(out), n


# A section heading already draws its own rule, so the "---" the Markdown puts
# above it lands as a second line 20px from the first. Dropping the <hr> is a
# presentation fix -- the separator is still there, once.
HR_BEFORE_H2 = re.compile(r"<hr\s*/?>\s*(?=<h2[ >])")


def dedupe_rules(html):
    """Drop the horizontal rule immediately above a section heading."""
    n = len(HR_BEFORE_H2.findall(html))
    return (HR_BEFORE_H2.sub("", html) if n else html), n


# Python-Markdown's fenced_code does not recognise a fence that is indented
# as list-item content: the backticks survive as literal text and the list
# breaks in half around them. An indented code block is the form it does
# understand inside a list, so the fence is rewritten into one before the
# Markdown is converted. Source files keep the fence, which is what every other
# renderer wants.
INDENTED_FENCE = re.compile(
    r"^(?P<pad>[ ]+)```[^\n]*\n(?P<body>.*?)^(?P=pad)```[ ]*$",
    re.M | re.S)


def unfence_in_lists(text):
    """Rewrite list-indented fences as indented code blocks. Returns (text, n)."""
    def one(m):
        pad = m.group("pad")
        # 4 spaces puts it inside the list item, 4 more make it a code block
        deep = pad + " " * 6
        lines = [deep + ln[len(pad):] if ln.startswith(pad) else deep + ln.lstrip()
                 for ln in m.group("body").rstrip("\n").split("\n")]
        return "\n".join(lines) + "\n"
    n = len(INDENTED_FENCE.findall(text))
    return (INDENTED_FENCE.sub(one, text) if n else text), n


# References support the page but are not part of its reading flow, so they
# fold away rather than sitting in the main scroll. The heading stays outside
# the fold so the rail still has something to land on and the section is still
# findable; only the list itself collapses. Nothing is removed.
REFS_H = re.compile(r'<h2 id="references"[^>]*>.*?</h2>', re.S)


def fold_references(html):
    """Collapse the trailing References list. Returns (html, count)."""
    m = REFS_H.search(html)
    if not m:
        return html, 0
    body = html[m.end():].strip()
    if not body:
        return html, 0
    return (html[:m.end()]
            + '<details class="refs"><summary>Show the sources this page was '
              'built from</summary><div class="refs-body">%s</div></details>' % body), 1


def tablecards(html):
    """Put every table in a bordered, horizontally scrollable card.

    A wide reference table sitting directly in the reading flow either squeezes
    its columns or pushes the whole page sideways on a phone; the card owns the
    overflow so the page itself never scrolls horizontally.
    """
    n = len(TABLE.findall(html))
    if n:
        html = TABLE.sub(lambda m: '<div class="table-card">%s</div>' % m.group(1), html)
    return html, n


def calloutify(html):
    """Style blockquotes as callouts, warnings distinguished from notes."""
    out, at, n = [], 0, 0
    while True:
        i = html.find("<blockquote>", at)
        if i < 0:
            out.append(html[at:])
            break
        j = html.index("</blockquote>", i) + len("</blockquote>")
        inner = html[i + len("<blockquote>"):j - len("</blockquote>")]
        lead = re.sub(r"<[^>]+>", " ", inner)[:120]
        kind = "callout--warning" if WARN.search(lead) else "callout--note"
        out.append(html[at:i])
        out.append('<aside class="callout %s">%s</aside>' % (kind, inner))
        at = j
        n += 1
    return "".join(out), n


def badgify(html):
    """Turn a section's Notebook/Lab credit line into a row of pills."""
    def one(m):
        parts = [s.strip() for s in re.split(r"\u00b7|&middot;", m.group(1)) if s.strip()]
        return ('<p class="badge-row">%s</p>'
                % "".join('<span class="badge">%s</span>' % s for s in parts))
    n = len(BADGES.findall(html))
    return (BADGES.sub(one, html) if n else html), n


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
H2 = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', re.S)
TITLE = re.compile(r'<h1 id="([^"]+)"[^>]*>(.*?)</h1>', re.S)
FAMILY = [
    (re.compile(r"^Part\s+(\d+)\s*[\u2014\u2013-]\s*(.*)$", re.S), "part"),
    (re.compile(r"^Tier\s+([A-Z])\s*[\u2014\u2013-]\s*(.*)$", re.S), "tier"),
    (re.compile(r"^Appendix\s+([A-Z])\s*[\u2014\u2013-]\s*(.*)$", re.S), "appendix"),
    # The roadmap explainers number their sections "1." .. "13." at <h2>.
    (re.compile(r"^(\d+)\.\s+(.*)$", re.S), "section"),
]


def rail_headings(html):
    """The headings the rail is built from.

    Documents here come in two shapes. The field guide and the question bank
    are one flat file whose sections are <h1> ("Part 3 -- Trajectory"); the
    roadmap explainers are a single <h1> title with numbered <h2> sections.
    Whichever level carries the sections is the one to index -- mixing both
    would list every subsection of a document that already has enough parts.
    """
    tops = H1.findall(html)
    if len(tops) >= DOCNAV_MIN:
        return tops
    subs = H2.findall(html)
    if len(subs) >= DOCNAV_MIN:
        return tops[:1] + subs
    return []


def github_slug(value, separator="-"):
    """Heading ids the way GitHub writes them, so a #fragment works in both places.

    Lowercase, drop punctuation (anything but word characters, spaces and
    hyphens), and turn each space into a hyphen without collapsing them:
    "Part 5 -- Online vs offline" -> "part-5--online-vs-offline". The docs link
    each other in that form; Python-Markdown's default collapses the "--".
    """
    return re.sub(r"[^\w\- ]", "", value.strip().lower()).replace(" ", separator)


LEVEL_TAG = re.compile(r"<(/?)h([1-6])\b")


def demote_extra_h1(html):
    """Keep the first <h1> and shift every later heading down one level (h6 caps).

    Five long documents carry their Parts as <h1>, which is right on GitHub and
    wrong on a web page: a page should have one <h1>. The Markdown stays as it is,
    and this runs after the rail and the question folds are built, so they see the
    levels they were written for. ids are untouched, so #anchors still land.
    """
    first = re.search(r"<h1\b", html)
    if not first or not re.search(r"<h1\b", html[first.end():]):
        return html
    end = html.index("</h1>", first.end()) + len("</h1>")
    rest = LEVEL_TAG.sub(lambda m: "<%sh%d" % (m.group(1), min(int(m.group(2)) + 1, 6)),
                         html[end:])
    return html[:end] + rest


def docnav(html):
    """Build the sticky section rail from the page's <h1>s. Returns (html, n).

    The first heading is the document title, which is not a section -- it
    becomes the rail's way back to the top, labelled Orientation to match the
    drill.
    """
    heads = rail_headings(html)
    if not heads:
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
            # A section that follows none of the naming schemes still belongs
            # in the rail; it just has no index to show. It shares the family
            # of the numbered ones so an unnumbered lead-in ("Why this level
            # exists") does not split the rail into three captioned groups.
            items.append(("section", "\u00b7", text, hid))

    items = [it for it in items if it[0] not in DOCNAV_SKIP]

    # Families are captioned rather than merely ruled off: Tier A..H indexes by
    # bare letter, and a lone column of letters names nothing.
    caption = {"part": "Parts", "tier": "Tiers", "section": "Sections", "": ""}
    out = ['<nav class="docnav" id="docnav" aria-label="Sections">']
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
    out.append("</ol>")
    # How far in you are, in the rail rather than as a bar across the top: the
    # question a reader asks here is "how much is left", which is a count of
    # sections, not a percentage of pixels.
    out.append('<div class="rail-progress" aria-hidden="true">'
               '<div class="rail-bar"><i></i></div>'
               '<span class="rail-count">Section 1 of %d</span></div>' % (len(items) - 1))
    out.append("</nav>")
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

  var fill = rail.querySelector(".rail-bar i");
  var count = rail.querySelector(".rail-count");
  var bar = document.querySelector("header.bar");

  var current = -1;
  function mark() {
    // The line a heading has to cross to count as current sits just below the
    // sticky header, so it moves with it rather than assuming one row.
    var line = (bar ? bar.getBoundingClientRect().height : 58) + 32, at = 0;
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

    // The first rail item is the title, not a section, so both the count and
    // the bar are measured against the sections that follow it.
    var total = links.length - 1;
    if (fill && total > 0) {
      fill.style.width = Math.round((at / total) * 100) + "%";
      if (count) { count.textContent = "Section " + Math.max(at, 1) + " of " + total; }
    }
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
  // The header's height decides the drawer's top edge and every anchor jump's
  // offset. It is not a constant -- the nav wraps at some widths and the
  // chapter row is only on some pages -- so it is measured rather than
  // guessed. The CSS carries a static fallback for when this does not run.
  if (bar) {
    var measure = function () {
      // Set on <body>, not <html>: the stylesheet's fallback is a rule on
      // body, and a value set on the ancestor would be shadowed by it for
      // every descendant that reads the token.
      document.body.style.setProperty(
        "--bar-h", Math.round(bar.getBoundingClientRect().height) + "px");
    };
    measure();
    if (window.ResizeObserver) { new ResizeObserver(measure).observe(bar); }
    else { addEventListener("resize", measure); }
  }

  var doc = document.querySelector("article.doc");
  if (doc && window.ResizeObserver) { new ResizeObserver(onScroll).observe(doc); }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(mark); }
  mark();

  // ---- the drawer on narrow screens ------------------------------------
  // The rail is navigation, so it is never dropped on a phone -- it becomes a
  // panel the Contents button opens. The button is hidden in the markup and
  // revealed here, so a reader without JS is not offered a control that would
  // do nothing.
  var toggle = document.querySelector(".toc-toggle");
  if (toggle) {
    toggle.hidden = false;
    var open = function (want) {
      document.body.classList.toggle("toc-open", want);
      toggle.setAttribute("aria-expanded", want ? "true" : "false");
    };
    toggle.addEventListener("click", function () {
      open(!document.body.classList.contains("toc-open"));
    });
    rail.addEventListener("click", function (e) {
      if (e.target.closest("a")) { open(false); }
    });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape") { open(false); }
    });
  }
})();
</script>

<script>
// ---- a copyable link on every heading ----------------------------------
// The ids are already there (the `toc` extension writes them); what is missing
// is a way to get at one without reading the source. Added here rather than in
// the Markdown so no document carries link markup of its own.
(function () {
  var heads = document.querySelectorAll("article.doc h1[id], article.doc h2[id], "
                                        + "article.doc h3[id], article.doc h4[id]");
  [].forEach.call(heads, function (h) {
    var a = document.createElement("a");
    a.className = "anchor";
    a.href = "#" + h.id;
    a.setAttribute("aria-label", "Link to this section");
    a.textContent = "#";
    a.addEventListener("click", function (e) {
      if (!navigator.clipboard) return;          // let the plain jump happen
      e.preventDefault();
      history.replaceState(null, "", a.href);
      h.scrollIntoView();
      navigator.clipboard.writeText(a.href).then(function () {
        a.classList.add("copied");
        setTimeout(function () { a.classList.remove("copied"); }, 1200);
      });
    });
    h.appendChild(a);
  });
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
HEAD_CLOSE = re.compile(r"</head>", re.I)
GOOGLE_FONTS = re.compile(r'<link[^>]*fonts\.(?:googleapis|gstatic)\.com[^>]*>\n?', re.I)
BODY_CLOSE = re.compile(r"</body>", re.I)
OWN_DESC = re.compile(r'<meta name="description" content="([^"]*)">\n?', re.I)


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


def chapter_row(group, pos, title):
    """The header's slim second row: where you are, and the way on.

    Prev/next come from the order of the section's own RENDER list, so adding a
    level in the right place is the only thing needed to wire it in -- there is
    no per-page copy of the sequence to fall out of step.
    """
    if len(group) < 2:
        return ""
    ends = []
    if pos:
        ends.append('<a class="prev" href="%s.html">&larr; %s</a>'
                    % (group[pos - 1][1], group[pos - 1][2]))
    if pos < len(group) - 1:
        ends.append('<a class="next" href="%s.html">%s &rarr;</a>'
                    % (group[pos + 1][1], group[pos + 1][2]))
    return ('<div class="chapter"><span class="here">%s</span>'
            '<span class="ends">%s</span></div>' % (title, "".join(ends)))


def shell(title, body, nav, head, foot, is_index=False, diagrams=0, qa=0, rail=0,
          chapter=""):
    home = "" if is_index else '<a class="home" href="index.html">&larr; All documents</a>'
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
%s
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<header class="bar">
  <div class="bar-top">
    <a class="brand" href="index.html">Agent Evaluation <span>Demystified</span></a>
    <button class="toc-toggle" type="button" aria-expanded="false"
            aria-controls="docnav" hidden>Contents</button>
    <nav>%s</nav>
  </div>
  %s
</header>
<main class="wrap">
%s
%s
</main>
%s%s
</body>
</html>
""" % (title, head, nav, chapter, home, body, foot,
       (MERMAID_SCRIPT if diagrams else "") + (QA_SCRIPT if qa else "")
       + (DOCNAV_SCRIPT if rail else ""))


def top_nav(active_section):
    out = []
    for s in SECTION_ORDER:
        cls = ' class="on"' if s == active_section else ""
        out.append('<a%s href="index.html#%s">%s</a>' % (cls, s.lower().replace(" ", "-"), s))
    return "".join(out)


# A page under docs/ in none of RENDER, COPY or SKIP fails the build. Set to False only
# to get a deploy out while a known straggler is being registered.
STRICT_COMPLETENESS = True


def docs_sources():
    """Every .md and .html under docs/ -- tracked files if git is available."""
    import subprocess
    try:
        out = subprocess.run(["git", "ls-files", "docs"], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout.split()
        files = [f[len("docs/"):] for f in out]
    except (OSError, subprocess.CalledProcessError):
        files = [os.path.relpath(os.path.join(d, f), DOCS)
                 for d, _, fs in os.walk(DOCS) for f in fs]
    return sorted(f for f in files if f.endswith((".md", ".html")))


def check_completeness():
    """Fail (or warn) on a docs/ page that is in none of RENDER, COPY, SITE_PAGES, SKIP.

    Without this, a new page under docs/ is silently never published.
    """
    known = ({s for g in RENDER.values() for s, *_ in g}
             | {s for g in COPY.values() for s, *_ in g}
             | {s for s, _ in SKIP}
             | {s for s, *_ in SITE_PAGES})
    missing = [f for f in docs_sources() if f not in known]
    if not missing:
        return
    msg = ("%d file(s) under docs/ are in none of RENDER, COPY, SITE_PAGES or SKIP:\n   %s"
           % (len(missing), "\n   ".join(missing)))
    if STRICT_COMPLETENESS:
        raise SystemExit(msg)
    print("WARNING: " + msg + "\n")


def build():
    # Imported here, not at the top, so stdlib-only tools (site/stamp_dates.py)
    # can import this module's page lists without markdown installed.
    try:
        import markdown
    except ImportError:
        sys.exit("markdown is not installed.  pip install -r site/requirements.txt")
    check_completeness()
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    # site/assets/ holds the share image and favicons; their source is site/og.html.
    shutil.copytree(os.path.join(ROOT, "site", "assets"), os.path.join(DIST, "assets"))
    shutil.copy(os.path.join(ROOT, "site", "site.css"),
                os.path.join(DIST, "assets", "site.css"))

    rendered, copied = [], []
    linked_paths = 0
    dates = json.load(io.open(os.path.join(ROOT, "site", "page-dates.json"), encoding="utf-8"))

    def render(src, slug, title, blurb, nav, chapter=""):
        """Markdown under docs/ -> site/dist/<slug>.html through the shared shell."""
        nonlocal linked_paths
        path = os.path.join(DOCS, src)
        text = io.open(path, encoding="utf-8").read()
        source, unfenced = unfence_in_lists(text)
        md = markdown.Markdown(extensions=["tables", "fenced_code", "toc",
                                           "sane_lists", "attr_list"],
                               extension_configs={"toc": {"slugify": github_slug}})
        html = pandoc_typography(md.convert(source))
        html = LINK.sub(
            lambda m: m.group(1) + rewrite_link(m.group(2), "docs/" + src) + m.group(3),
            html)
        html, paths = linkify_code_paths(html)
        linked_paths += paths
        html = titlify_site_links(html)
        html, diagrams = mermaidise(html)
        html, plains = plainify(html)
        html, questions = collapsify(html)
        html, _answers = hide_answers(html)
        html, badges = badgify(html)
        html, _rules = dedupe_rules(html)
        html, callouts = calloutify(html)
        html, examples = worked_examples(html)
        html, refs = fold_references(html)
        html, tables = tablecards(html)
        rail, sections = docnav(html)
        html = demote_extra_h1(html)
        article = '<article class="doc">%s</article>' % html
        body = '<div class="withnav">%s%s</div>' % (rail, article) if rail else article
        title_text = re.sub("<[^>]+>", "", title)
        page = shell(title_text, body, nav,
                     head_tags(slug + ".html", title_text, re.sub("<[^>]+>", "", blurb),
                               dates.get("docs/" + src)),
                     footer("docs/" + src, dates.get("docs/" + src)),
                     diagrams=diagrams, qa=questions, rail=sections,
                     chapter=chapter)
        io.open(os.path.join(DIST, slug + ".html"), "w", encoding="utf-8").write(page)
        rendered.append((src, slug + ".html", len(text.split()), diagrams,
                         questions, plains, sections, tables, callouts,
                         badges, examples))

    for section in SECTION_ORDER:
        group = RENDER.get(section, [])
        for pos, (src, slug, title, blurb) in enumerate(group):
            render(src, slug, title, blurb, top_nav(section), chapter_row(group, pos, title))

        for src, title, blurb in COPY.get(section, []):
            # Copied pages carry links written for their old home under docs/ --
            # a .md target, or a folder-relative path. Rewrite them the same way
            # as rendered pages so the flat site has no dead links.
            text = io.open(os.path.join(DOCS, src), encoding="utf-8").read()
            text = LINK.sub(
                lambda m: m.group(1) + rewrite_link(m.group(2), "docs/" + src) + m.group(3),
                text)
            text, paths = linkify_code_paths(text)
            linked_paths += paths
            text = titlify_site_links(text)
            # The page's own <title> (more specific than the nav title) and its own
            # description, when it has one, become the share tags. The original
            # description goes, so it isn't there twice.
            own_title = re.search(r"<title>(.*?)</title>", text, re.S).group(1).strip()
            text = GOOGLE_FONTS.sub("", text)  # head_tags() links the self-hosted copies
            desc = OWN_DESC.search(text)
            text = OWN_DESC.sub("", text)
            tags = head_tags(copied_name(src), own_title, desc.group(1) if desc else blurb,
                             dates.get("docs/" + src))
            text, n = HEAD_CLOSE.subn(lambda m: tags + "\n" + m.group(0), text)
            if n != 1:
                raise SystemExit("expected one </head> to attach the head tags to: %s" % src)
            foot = footer("docs/" + src, dates.get("docs/" + src))
            text, n = BODY_CLOSE.subn(lambda m: foot + "\n" + m.group(0), text)
            if n != 1:
                raise SystemExit("expected one </body> to attach the footer to: %s" % src)
            text, n = BODY_OPEN.subn(lambda m: m.group(1) + "\n" + sitebar(), text, count=1)
            if not n:
                raise SystemExit("no <body> to attach the nav bar to: %s" % src)
            io.open(os.path.join(DIST, copied_name(src)), "w", encoding="utf-8").write(text)
            copied.append((src, copied_name(src)))

    # Site pages (about, changelog): the same rendering, but no index card and no nav section.
    for src, slug, title, blurb in SITE_PAGES:
        render(src, slug, title, blurb, top_nav(None))

    # ---- index
    topics = roadmap_topics()
    cards = []
    for section in SECTION_ORDER:
        items = []
        for src, slug, title, blurb in RENDER.get(section, []):
            # Explainer cards carry the level's topics instead of a word count:
            # "what is in here" is the thing a reader is choosing on, and a
            # length was never the reason to open one rather than another.
            if section == "Roadmap explainers":
                items.append('<li><a href="%s.html">%s</a><p>%s</p>%s</li>'
                             % (slug, title, blurb, topics_html(slug, topics)))
                continue
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

    # The first screen names the reader, the promise and one thing to press
    # (ON-01); the secondary button is the interview lane (ON-05). Copy is the
    # owner-approved UX-01 draft.
    body = """<p class="eyebrow">For engineers who ship RAG systems and agents &mdash; or answer
for them in an interview</p>
<h1>Agent Evaluation Demystified</h1>
<p class="lede hero-lede">How do you know your RAG system or agent is actually working? Measure
it layer by layer (retrieval, generation, tools, the path an agent takes), gate releases on it,
and keep watching it in production.</p>
<p class="cta"><a class="btn primary" href="00-orientation.html">Start at Level 0</a>
<a class="btn" href="evaluation-study-plan.html#fast">Interviewing this week?</a></p>
<p class="repo-note">The notebooks live in <a href="%(repo)scourses/">the repository</a>.</p>
<ul class="paths">
<li><span class="path-t">Learn it in order.</span> Level 0 to Level 10: eleven explainers, six
labs and the notebooks behind them. About 54 hours.
<span class="go"><a href="roadmap.html">The roadmap &rarr;</a></span></li>
<li><span class="path-t">Cram for an interview.</span> The study plan&rsquo;s fast path, then the
drill on what&rsquo;s still weak. About 10 hours.
<span class="go"><a href="evaluation-study-plan.html#fast">The fast path &rarr;</a></span></li>
<li><span class="path-t">Look up one thing.</span> The field guide for any metric; the question
bank for any interview question.
<span class="go"><a href="field-guide.html">Field guide &rarr;</a> &middot; <a href="question-bank.html">Question bank &rarr;</a></span></li>
</ul>
%(cards)s""" % {"repo": REPO_URL, "cards": "".join(cards)}

    io.open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(
        shell("Agent Evaluation Demystified", body, top_nav(None),
              head_tags("index.html", "Agent Evaluation Demystified",
                        "Written companions to a hands-on course in evaluating RAG "
                        "systems and agents.", kind="website"),
              footer(date=max(dates.values())),
              is_index=True))

    # ---- 404: Vercel serves it for any unknown path, even /a/b/c, so <base> makes
    # its relative links (stylesheet, nav, footer) resolve from the root.
    sections = "".join('<li><a href="index.html#%s">%s</a></li>'
                       % (s.lower().replace(" ", "-"), s) for s in SECTION_ORDER)
    body = """<article class="doc"><h1>This page doesn&rsquo;t exist</h1>
<p>The link may be old, or the address mistyped. Every page is one of these sections:</p>
<ul>%s</ul>
<p><a href="00-orientation.html">Start at Level 0 &rarr;</a></p></article>""" % sections
    io.open(os.path.join(DIST, "404.html"), "w", encoding="utf-8").write(
        shell("Page not found &middot; Agent Evaluation Demystified", body, top_nav(None),
              '<base href="/">\n' + head_tags("404.html", "Page not found",
                                               "This page doesn't exist.", kind="404"),
              footer(), is_index=True))

    # ---- robots.txt and sitemap.xml, from the pages written this run
    pages = ([(out, dates.get("docs/" + src)) for src, out, *_ in rendered]
             + [(out, dates.get("docs/" + src)) for src, out in copied]
             + [("index.html", max(dates.values()))])
    urls = "".join("<url><loc>%s</loc><lastmod>%s</lastmod></url>\n"
                   % (xml_escape(page_url(out)), date) for out, date in pages)
    io.open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)
    io.open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE_URL)

    # ---- report
    print("rendered from Markdown:")
    for src, out, w, d, q, pl, sec, tb, co, bg, ex in rendered:
        extra = "  ".join(x for x in (("%d diagrams" % d) if d else "",
                                      ("%d collapsible" % q) if q else "",
                                      ("%d plain-English" % pl) if pl else "",
                                      ("%d-item rail" % sec) if sec else "",
                                      ("%d tables" % tb) if tb else "",
                                      ("%d callouts" % co) if co else "",
                                      ("%d badges" % bg) if bg else "",
                                      ("%d examples" % ex) if ex else "") if x)
        print("   %-48s -> %-26s %6s words  %s"
              % (src, out, "{:,}".format(w), extra))
    print("\ncopied as-is (interactive, not producible from Markdown):")
    for src, out in copied:
        print("   %-48s -> %s" % (src, out))
    print("\nskipped on purpose:")
    for src, why in SKIP:
        print("   %-48s %s" % (src, why[:60] + ("..." if len(why) > 60 else "")))
    print("\n%d repo-path code spans turned into links" % linked_paths)
    print("\n%d pages in site/dist/  (%d rendered, %d copied, 1 index)"
          % (len(rendered) + len(copied) + 1, len(rendered), len(copied)))


if __name__ == "__main__":
    build()
