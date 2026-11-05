"""Render every week's theory Markdown into HTML beside it, in the repository site's format.

Usage, from new_course/ (needs `markdown`, in requirements-core.txt):
    python3 tools/build_html.py            # write weeks/*/theory/*-theory.html
    python3 tools/build_html.py --check    # exit 1 if any HTML is out of date

The page goes through the same transforms as the published field guide (site/build.py):
section rail, callouts, worked-example panels, table cards, collapsible design-review
questions, hidden Check Yourself answers and folded references. It links the site's own
stylesheets and fonts by relative path, so it renders from a clone of the repository.

The Markdown is the source. Never edit the HTML by hand: edit the Markdown and rerun.
"""

from __future__ import annotations

import html as htmllib
import importlib.util
import os
import re
import sys
from pathlib import Path

import markdown

TOOLS = Path(__file__).resolve().parent
COURSE = TOOLS.parent
SITE = COURSE.parent / "site"

sys.path.insert(0, str(SITE))  # site/build.py imports site/head.py
_spec = importlib.util.spec_from_file_location("site_build", SITE / "build.py")
site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(site)

MD_LINK = re.compile(r'href="([^"#:]+)\.md(#[^"]*)?"')
WEEK_NAME = re.compile(r"^week-(\d+)-")


def _rel(target: Path, page_dir: Path) -> str:
    return os.path.relpath(target, page_dir).replace(os.sep, "/")


def _theory_twin(href: str, page_dir: Path) -> str:
    """Point a link to another week's theory Markdown at its HTML page."""
    def one(m: re.Match) -> str:
        target, anchor = m.group(1), m.group(2) or ""
        return f'href="{target}.html{anchor}"' if target.endswith("-theory") else m.group(0)
    return MD_LINK.sub(one, href)


def _week_title(md_path: Path) -> str:
    title = re.search(r"^# (.+)$", md_path.read_text(), re.M).group(1)
    return title.replace(" theory: ", " &middot; ", 1)


def _header(md_path: Path) -> str:
    page_dir = md_path.parent
    week_dir = page_dir.parent
    slug = week_dir.name
    weeks = theory_files()
    pos = weeks.index(md_path)
    ends = []
    if pos:
        ends.append(f'<a class="prev" href="{_rel(weeks[pos - 1].with_suffix(".html"), page_dir)}">'
                    f'&larr; {_week_title(weeks[pos - 1])}</a>')
    else:
        ends.append(f'<a class="prev" href="{_rel(COURSE / "README.md", page_dir)}">&larr; Course index</a>')
    if pos < len(weeks) - 1:
        ends.append(f'<a class="next" href="{_rel(weeks[pos + 1].with_suffix(".html"), page_dir)}">'
                    f'{_week_title(weeks[pos + 1])} &rarr;</a>')
    nav = "".join([
        f'<a class="on" href="{md_path.with_suffix(".html").name}">Theory</a>',
        f'<a href="../handson/{slug}-handson.md">Hands-on</a>',
        f'<a href="../handson/{slug}-handson.ipynb">Notebook</a>',
        '<a href="../dataset/README.md">Dataset</a>',
    ])
    return f"""<header class="site-bar">
  <div class="bar-top">
    <a class="brand" href="{_rel(COURSE / "README.md", page_dir)}">Enterprise RAG &amp; Agent <span>Evaluation</span></a>
    <button class="toc-toggle" type="button" aria-expanded="false"
            aria-controls="docnav" hidden>Contents</button>
    <nav aria-label="Week">{nav}</nav>
  </div>
  <div class="chapter"><span class="here">{_week_title(md_path)}</span><span class="ends">{"".join(ends)}</span></div>
</header>"""


def render(md_path: Path) -> str:
    """The site's render pipeline (site/build.py, build.render) for one theory file."""
    md_path = md_path.resolve()
    text = md_path.read_text()
    source, _unfenced = site.unfence_in_lists(text)
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list"],
                           extension_configs={"toc": {"slugify": site.github_slug}})
    body = site.pandoc_typography(md.convert(source))
    body = _theory_twin(body, md_path.parent)
    body, diagrams = site.mermaidise(body)
    body, questions = site.collapsify(body)
    body, _answers = site.hide_answers(body)
    body, _badges = site.badgify(body)
    body, _rules = site.dedupe_rules(body)
    body, _callouts = site.calloutify(body)
    body, _examples = site.worked_examples(body)
    body = site.add_read_time(body)
    body, _refs = site.fold_references(body)
    body, _tables = site.tablecards(body)
    rail, sections = site.docnav(body)
    body = site.demote_extra_h1(body)
    article = f'<article class="doc">{body}</article>'
    content = f'<div class="withnav">{rail}{article}</div>' if rail else article

    assets = _rel(SITE / "assets", md_path.parent)
    css = _rel(SITE / "site.css", md_path.parent)
    title = re.sub("<[^>]+>", "", _week_title(md_path)).replace("&middot;", "·")
    scripts = ((site.MERMAID_SCRIPT if diagrams else "") + (site.QA_SCRIPT if questions else "")
               + (site.DOCNAV_SCRIPT if sections else ""))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{htmllib.escape(title)}</title>
<link rel="stylesheet" href="{assets}/fonts.css">
<link rel="icon" href="{assets}/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{assets}/tokens.css">
<link rel="stylesheet" href="{assets}/chrome.css">
<link rel="stylesheet" href="{css}">
</head>
<body>
{site.SKIP_LINK}
{_header(md_path)}
<main class="wrap" id="main">
<a class="home" href="{_rel(COURSE / "README.md", md_path.parent)}">&larr; Course index</a>
{content}
</main>
<footer class="aed-foot"><ul><li>Rendered from {md_path.name} by tools/build_html.py. Edit the Markdown, not this file.</li></ul></footer>
{scripts}
</body>
</html>
"""


def theory_files() -> list[Path]:
    return sorted(COURSE.glob("weeks/*/theory/*-theory.md"))


def main() -> None:
    check = "--check" in sys.argv[1:]
    stale = []
    for md_path in theory_files():
        out = md_path.with_suffix(".html")
        page = render(md_path)
        if check:
            if not out.exists() or out.read_text() != page:
                stale.append(str(out.relative_to(COURSE)))
        else:
            out.write_text(page)
            print(f"wrote {out.relative_to(COURSE)}")
    if stale:
        sys.exit(f"out of date, run python3 tools/build_html.py: {stale}")


if __name__ == "__main__":
    main()
