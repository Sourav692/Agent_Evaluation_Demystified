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

SECTION_ORDER = ["Theory", "Interview prep", "Audits", "Interactive labs"]


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


def shell(title, body, nav, blurb="", is_index=False):
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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Zilla+Slab:wght@500;600&display=swap" rel="stylesheet">
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
</footer>
</body>
</html>
""" % (title, blurb, nav, home, body)


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
            page = shell(re.sub("<[^>]+>", "", title), '<article class="doc">%s</article>' % html,
                         top_nav(section), re.sub("<[^>]+>", "", blurb))
            io.open(os.path.join(DIST, slug + ".html"), "w", encoding="utf-8").write(page)
            rendered.append((src, slug + ".html", len(text.split())))

        for src, title, blurb in COPY.get(section, []):
            # Copied pages carry links written for their old home under docs/ --
            # a .md target, or a folder-relative path. Rewrite them the same way
            # as rendered pages so the flat site has no dead links.
            text = io.open(os.path.join(DOCS, src), encoding="utf-8").read()
            text = LINK.sub(
                lambda m: m.group(1) + rewrite_link(m.group(2), "docs/" + src) + m.group(3),
                text)
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
            items.append('<li><a href="%s">%s</a><span class="meta">interactive</span>'
                         '<p>%s</p></li>' % (copied_name(src), title, blurb))
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
    for src, out, w in rendered:
        print("   %-48s -> %-26s %6s words" % (src, out, "{:,}".format(w)))
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
