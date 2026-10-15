"""The <head> tags and the footer every page shares: description, share preview,
canonical, self-hosted fonts, favicons, JSON-LD, and who maintains the page and when it changed. Used by shell() for rendered pages and injected into the
copied pages, so a shared link previews the same way from either family.

Titles and descriptions arrive as HTML text (the RENDER and COPY lists hold
entities such as &amp; and &middot;), so they are unescaped once and then
escaped for the context they land in.
"""
import html
import json

SITE_URL = "https://eval-demystified.vercel.app"
AUTHOR = "Sourav Banerjee"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
REPO = "https://github.com/Sourav692/Agent_Evaluation_Demystified"


def page_url(filename):
    """Absolute URL of a page in the flat site; index.html is the root."""
    return SITE_URL + "/" + ("" if filename == "index.html" else filename)


def attr(text):
    return html.escape(html.unescape(text), quote=True)


def json_ld(filename, title, description, date):
    data = {
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": html.unescape(title),
        "description": html.unescape(description),
        "url": page_url(filename),
        "inLanguage": "en",
        "author": {"@type": "Person", "name": AUTHOR},
        "license": LICENSE_URL,
    }
    if date:
        data["dateModified"] = date
    # "</" would close the <script> early if a title ever contained it.
    return ('<script type="application/ld+json">%s</script>'
            % json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


def head_tags(filename, title, description, date=None, kind="article"):
    """kind: "article" (a page, with JSON-LD), "website" (the index) or "404"."""
    tags = ['<meta name="description" content="%s">' % attr(description)]
    if kind == "404":
        tags.append('<meta name="robots" content="noindex">')
    else:
        url = page_url(filename)
        tags += [
            '<link rel="canonical" href="%s">' % url,
            '<meta property="og:type" content="%s">' % kind,
            '<meta property="og:site_name" content="Agent Evaluation Demystified">',
            '<meta property="og:title" content="%s">' % attr(title),
            '<meta property="og:description" content="%s">' % attr(description),
            '<meta property="og:url" content="%s">' % url,
            '<meta property="og:image" content="%s/assets/og.png">' % SITE_URL,
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:alt" content="Agent Evaluation Demystified">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
    tags += ['<link rel="preload" href="assets/fonts/newsreader.woff2" as="font" '
             'type="font/woff2" crossorigin>',
             '<link rel="stylesheet" href="assets/fonts.css">',
             '<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">',
             '<link rel="icon" href="assets/favicon-32.png" sizes="32x32" type="image/png">']
    # Vercel Web Analytics: cookieless page views, same origin. 404s locally and
    # until the analytics are enabled on the project; harmless either way.
    tags.append('<script defer src="/_vercel/insights/script.js"></script>')
    if kind == "article":
        tags.append(json_ld(filename, title, description, date))
    return "\n".join(tags)


# Literal colours, scoped to .aed-foot, for the same reason as build.py's SITEBAR:
# the copied pages bring their own stylesheet and don't define the site's tokens.
FOOT_STYLE = """<style>
.aed-foot{max-width:1320px;margin:0 auto;padding:24px clamp(16px,3vw,28px) 56px;
  border-top:1px solid #C5C8C2;color:#3C4E51;
  font:15.5px/1.6 "Newsreader",Georgia,serif}
.aed-foot ul{display:flex;flex-wrap:wrap;gap:4px 0;margin:0;padding:0;list-style:none}
.aed-foot li+li::before{content:"\\00B7";padding:0 10px}
.aed-foot a{color:inherit;text-underline-offset:3px}
.aed-foot a:hover{color:#0E2226}
.aed-foot a:focus-visible{outline:2px solid #9A6A12;outline-offset:3px;border-radius:2px}
@media (prefers-color-scheme:dark){
  .aed-foot{border-top-color:#26383B;color:#9FB1B1}
  .aed-foot a:hover{color:#DDE5E3}
  .aed-foot a:focus-visible{outline-color:#D3A54C}
}
@media print{.aed-foot{display:none}}
</style>"""


def footer(src=None, date=None):
    """src is the page's repo path (docs/...); the index passes none and gets no Edit link."""
    items = ["Maintained by %s" % AUTHOR]
    if date:
        items.append('Last updated <time datetime="%s">%s</time>' % (date, date))
    if src:
        items.append('<a href="%s/edit/main/%s">Edit on GitHub</a>' % (REPO, src))
    items += ['<a href="%s/issues/new">Report an issue</a>' % REPO,
              '<a href="about.html">About</a>',
              '<a href="changelog.html">Changelog</a>']
    return '%s\n<footer class="aed-foot"><ul>%s</ul></footer>' % (
        FOOT_STYLE, "".join("<li>%s</li>" % i for i in items))

if __name__ == "__main__":
    t = head_tags("x.html", "MLflow &amp; Databricks", 'Say "hi" </script>', "2026-10-15")
    assert 'content="MLflow &amp; Databricks"' in t  # entity not double-escaped
    # a "</script>" in the description can't close the JSON-LD early
    assert json_ld("x.html", "t", "a </script>", None).count("</script>") == 1
    assert '"dateModified": "2026-10-15"' in t
    assert "noindex" in head_tags("404.html", "Not found", "d", kind="404")
    assert 'href="https://eval-demystified.vercel.app/"' in head_tags("index.html", "t", "d", kind="website")
    f = footer("docs/about.md", "2026-10-15")
    assert '<time datetime="2026-10-15">' in f and "/edit/main/docs/about.md" in f
    assert "Edit on GitHub" not in footer(date="2026-10-15")
    print("self-test ok")
