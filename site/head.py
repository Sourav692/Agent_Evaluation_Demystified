"""The <head> tags every page shares: description, share preview, canonical,
favicons, and JSON-LD. Used by shell() for rendered pages and injected into the
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
    tags += ['<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">',
             '<link rel="icon" href="assets/favicon-32.png" sizes="32x32" type="image/png">']
    if kind == "article":
        tags.append(json_ld(filename, title, description, date))
    return "\n".join(tags)


if __name__ == "__main__":
    t = head_tags("x.html", "MLflow &amp; Databricks", 'Say "hi" </script>', "2026-10-15")
    assert 'content="MLflow &amp; Databricks"' in t  # entity not double-escaped
    assert t.count("</script>") == 1  # the description's "</script>" can't close the JSON-LD early
    assert '"dateModified": "2026-10-15"' in t
    assert "noindex" in head_tags("404.html", "Not found", "d", kind="404")
    assert 'href="https://eval-demystified.vercel.app/"' in head_tags("index.html", "t", "d", kind="website")
    print("self-test ok")
