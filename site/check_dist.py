#!/usr/bin/env python3
"""Fail the build when site/dist/ has drifted from what the site promises.

Runs after build.py, on Vercel and in CI. Each failure prints
`<file>: <rule>: <detail>` and the script exits 1.

    python3 site/check_dist.py              check site/dist/
    python3 site/check_dist.py --self-test

Rules, one function each:
  head         share preview, canonical, description on every page (404: noindex instead)
  one-h1       exactly one <h1>
  build-note   the old "Generated from the Markdown" footer is gone
  repo-path    no docs/... path shown as text (code span outside a link, <pre>, <script>),
               nor (docs/ path or bare .md name) as the text of a link to a site page
  blob-link    no GitHub blob link to a doc the site serves itself
  link         every relative <a href> resolves to a built file, and its #fragment to an id
  cdn-pin      every jsDelivr npm URL names an exact x.y.z version
  pandoc       no literal \\$ or --- in page text (Pandoc's escape and em dash)
  answers      every Check Yourself item's answer sits behind "Show answer"
  practise     every roadmap explainer has its "Practise it" section (lab or notebook links)
  names        each index card title is the short form of its page's H1 (a lab's eyebrow)

Stdlib only.
"""
import glob
from html import unescape as html_unescape
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import COPY, DIST, RENDER, REPO_URL, SITE_PAGES  # noqa: E402

SCRIPT = re.compile(r"<script\b.*?</script>", re.S)
HEAD_TAGS = ['property="og:title"', 'property="og:description"', 'property="og:image"',
             'property="og:url"', 'rel="canonical"', 'name="description"',
             'name="twitter:card"']
SERVED = {"docs/" + s for g in [*RENDER.values(), *COPY.values(), SITE_PAGES] for s, *_ in g}


def head(name, html, ctx):
    if name == "404.html":
        return [] if 'name="robots" content="noindex"' in html else ["no noindex"]
    return ["missing %s" % t for t in HEAD_TAGS if t not in html]


def one_h1(name, html, ctx):
    n = len(re.findall(r"<h1\b", SCRIPT.sub("", html)))
    return [] if n == 1 else ["%d <h1> elements" % n]


def build_note(name, html, ctx):
    return ["build note still present"] if "Generated from the Markdown" in html else []


def repo_path(name, html, ctx):
    text = re.sub(r"<(pre|script|a)\b.*?</\1>", "", html, flags=re.S)
    shown = ["%s shown as text" % p for p in re.findall(r"<code>(docs/[^<]*)</code>", text)]
    # a link to one of the site's own pages should read as its title, not its repo path
    site = re.findall(r'<a href="([^":#]+\.html)[^"]*"><code>(docs/[^<]*|[^<\s/]+\.md)</code>[^<]*</a>',
                      SCRIPT.sub("", html))
    return shown + ["%s is the link text for %s" % (p, h) for h, p in site]


def blob_link(name, html, ctx):
    return ["links GitHub for %s" % p for p in re.findall(r'href="%s(docs/[^"#]+)' % re.escape(REPO_URL), html)
            if p in SERVED]


def link(name, html, ctx):
    out = []
    for href in re.findall(r'<a\b[^>]*\bhref="([^"]*)"', SCRIPT.sub("", html)):
        if re.match(r"[a-z]+:|//|/_vercel/", href):
            continue  # external, mailto, Vercel's own endpoints
        path, _, frag = href.partition("#")
        target = os.path.basename(path) if path else name
        if path and not ctx["files"].get(path.lstrip("/"), False):
            out.append("broken link %s" % href)
        elif frag and target in ctx["ids"] and frag not in ctx["ids"][target]:
            out.append("no #%s in %s" % (frag, target))
    return out


def cdn_pin(name, html, ctx):
    return ["unpinned %s" % u for u, v in re.findall(r"(cdn\.jsdelivr\.net/npm/[^@\"'\s/]+@?([^/\"'\s]*))", html)
            if not re.fullmatch(r"\d+\.\d+\.\d+", v)]


CODE_ZONES = re.compile(r"<(pre|code|script|style)\b.*?</\1>", re.S)


def pandoc(name, html, ctx):
    text = CODE_ZONES.sub("", html)
    return (["%d literal \\$" % text.count("\\$")] if "\\$" in text else []) + \
           (["literal --- in %r" % m for m in re.findall(r".{0,30}[\s\w]---[\s\w].{0,30}", text)])


def answers(name, html, ctx):
    m = re.search(r'<h2 id="check-yourself">(.*?)(?=<h2\b|\Z)', html, re.S)
    if not m:
        return []
    items, folded = m.group(1).count("<li>"), m.group(1).count('<details class="answer">')
    return [] if items == folded else ["%d of %d Check Yourself answers shown inline" % (items - folded, items)]


EXPLAINERS = {slug + ".html" for _, slug, _, _ in RENDER.get("Roadmap explainers", [])}


def practise(name, html, ctx):
    if name not in EXPLAINERS:
        return []
    m = re.search(r'<h2 id="practise-it">.*?(?=<h2\b)', html, re.S)
    return [] if m and "<a " in m.group(0) else ["no Practise it section with links"]


def words(s):
    """'Level 4 &middot; Judges &amp; the humans' -> 'judges and the humans' (comparable form)."""
    s = html_unescape(re.sub(r"<[^>]+>", "", s)).lower().replace("&", " and ")
    s = re.sub(r"^level \d+ \W+ ", "", s)
    s = re.sub(r"\bthe\b", " ", re.sub(r"[^a-z0-9 ]+", " ", s.replace("-", "")))
    return " ".join(s.split())


def names(name, html, ctx):
    """Index only: a card's title must start its page's H1, or the H1 its title (IA-04)."""
    if name != "index.html":
        return []
    out = []
    for href, card in re.findall(r'<li><a href="([^"#]+\.html)">(.*?)</a>', html):  # the cards
        page = ctx["pages"].get(href, "")
        m = re.search(r'<div class="eyebrow">(.*?)</div>', page) or re.search(r"<h1\b[^>]*>(.*?)</h1>", page, re.S)
        if not m:
            continue
        a, b = words(card), words(m.group(1))
        if not (b.startswith(a) or a.startswith(b)):
            out.append("card %r vs %r on %s" % (html_unescape(card), html_unescape(re.sub("<[^>]+>", "", m.group(1))).strip(), href))
    return out


RULES = [head, one_h1, build_note, repo_path, blob_link, link, cdn_pin, pandoc, answers, practise, names]


def context(pages):
    """pages: {name: html}. Every built file, and the ids of each page."""
    files = {os.path.relpath(p, DIST): True for p in glob.glob(os.path.join(DIST, "**"), recursive=True)
             if os.path.isfile(p)}
    files.update({n: True for n in pages})
    ids = {n: set(re.findall(r'\bid="([^"]+)"', h)) for n, h in pages.items()}
    return {"files": files, "ids": ids, "pages": pages}


def check(pages):
    ctx = context(pages)
    return ["%s: %s: %s" % (n, rule.__name__.replace("_", "-"), d)
            for n, h in sorted(pages.items()) for rule in RULES for d in rule(n, h, ctx)]


def self_test():
    ok = ('<head><meta name="description" content="d"><link rel="canonical" href="x">'
          '<meta property="og:title" content="t"><meta property="og:description" content="d">'
          '<meta property="og:image" content="i"><meta property="og:url" content="u">'
          '<meta name="twitter:card" content="c"></head><h1 id="top">T</h1>'
          '<p><a href="b.html#s">b</a> <a href="#top">top</a></p>')
    b = ok.replace("#top", "#s").replace('id="top"', 'id="s"')
    assert check({"a.html": ok, "b.html": b}) == [], check({"a.html": ok, "b.html": b})
    cases = {
        "head": ok.replace('<meta property="og:image" content="i">', ""),
        "one-h1": ok + "<h1>again</h1>",
        "build-note": ok + "<p>Generated from the Markdown in docs/</p>",
        "repo-path": ok + "<p><code>docs/x.md</code></p>",
        "blob-link": ok + '<a href="%sdocs/about.md">x</a>' % REPO_URL,
        "link": ok + '<a href="missing.html">x</a><a href="b.html#nope">y</a>',
        "cdn-pin": ok + '<script src="https://cdn.jsdelivr.net/npm/mermaid@11/x.js"></script>',
        "pandoc": ok + "<h2>System --- Gating</h2><p>Acme \\$2,900</p>",
        "answers": ok + '<h2 id="check-yourself">C</h2><ol><li>Q? <strong>A.</strong></li></ol>',
    }
    for rule, html in cases.items():
        hits = [e for e in check({"a.html": html, "b.html": b}) if e.startswith("a.html: %s:" % rule)]
        assert hits, "rule %s did not fire" % rule
    for text in ("<code>docs/b.md</code>", "<code>b.md</code>, Part 5"):
        site_link = ok + '<p><a href="b.html#s">%s</a></p>' % text
        assert any("repo-path" in e for e in check({"a.html": site_link, "b.html": b})), text
    assert any("pandoc" in e for e in check({"a.html": ok + "<p>layer---tenant</p>", "b.html": b}))
    # what each rule must leave alone
    quiet = ok + ("<pre><code>docs/x.md</code></pre><a href=\"y\"><code>docs/x.md</code></a>"
                  "<script>s='<code>docs/x.md</code><h1>'</script>"
                  '<a href="https://example.com/z.html">e</a><a href="mailto:x@y">m</a>'
                  '<script src="https://cdn.jsdelivr.net/npm/mermaid@11.17.2/x.js"></script>'
                  "<pre>a --- b \\$1</pre><code>\\$x</code>")
    assert [e for e in check({"a.html": quiet, "b.html": b}) if "a.html" in e and "link" not in e] == []
    assert head("404.html", '<meta name="robots" content="noindex">', None) == []
    assert practise("00-orientation.html", "<h1>x</h1>", None) and not practise("a.html", "", None)
    card = '<ul class="cards"><li><a href="b.html">%s</a></li></ul></section>'
    assert names("index.html", card % "The self-quiz drill", {"pages": {"b.html": "<h1>The Evaluation Round</h1>"}})
    assert not names("index.html", card % "Level 4 &middot; Judges &amp; the humans",
                     {"pages": {"b.html": "<h1>Judges, and the Humans Who Validate Them</h1>"}})
    print("self-test ok")


def main(argv):
    if "--self-test" in argv:
        return self_test()
    pages = {os.path.basename(p): open(p, encoding="utf-8").read()
             for p in glob.glob(os.path.join(DIST, "*.html"))}
    if not pages:
        sys.exit("site/dist/ has no pages -- run site/build.py first")
    errors = check(pages)
    for e in errors:
        print(e)
    if errors:
        sys.exit("\n%d problem(s) in site/dist/" % len(errors))
    print("site/dist/ OK -- %d pages, %d rules" % (len(pages), len(RULES)))


if __name__ == "__main__":
    main(sys.argv[1:])
