#!/usr/bin/env python3
"""Crawl the Agent Evaluation Demystified site and run every audit check that
can be decided from served HTML. Standard library only.

The site has no sitemap today, so pages are found by following internal links
from the index (breadth first). If a sitemap.xml appears, its URLs are added to
the queue and PR-09 compares the two sets.

Page kinds, taken from how site/build.py builds them:
  home        / (index.html)
  explainer   rendered page whose <title> starts "Level N" (roadmap explainers)
  lab         copied page at /0N-<slug>.html that is not an explainer
  doc         any other rendered page (has <header class="bar">)
  standalone  any other copied page (drill, study plan, tutorial, ...)

Outputs (in --out):
  inventory.json     every page: status, timing, kind, title, H1s, meta, word
                     count, pattern hits; plus site-level facts (robots,
                     sitemap, 404, headers, top nav, broken links)
  scan-checks.json   suggested status + evidence per check ID (data/checks.json)
  scan-summary.md    the same, readable, with offending URLs
  redirects.json     only with --legacy: how each retired URL now responds

The scan suggests; it does not decide. Every suggestion is confirmed by reading
pages or in the browser before it goes into scores.json (see SKILL.md).

Usage:
  python3 crawl_inventory.py --base https://eval-demystified.vercel.app --out .website_spec/site-audits/2026-10-14
  python3 crawl_inventory.py --base URL --out DIR --limit 10           # quick sample
  python3 crawl_inventory.py --base URL --out DIR --legacy retired-urls.txt
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import string
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

UA = "eval-site-audit/1.0 (site owner audit)"

HOME_PATHS = {"/", "/index.html"}
EXPLAINER_TITLE = re.compile(r"^Level\s+(\d+)\b")
LAB_PATH = re.compile(r"^/0\d-[a-z0-9-]+\.html$")
SEQ_NUM = re.compile(r"^/(\d{2})-")
PAGE_EXT = re.compile(r"(\.html?|/[^./]*)$")  # pages, not assets
GOOD_URL = re.compile(r"^/(?:[a-z0-9]+(?:-[a-z0-9]+)*\.html)?$")

LEAK = [
    ("generated-from footer", re.compile(r"Generated from", re.I)),
    ("docs/ source path", re.compile(r"\bdocs/[\w./-]+\.(?:md|html)\b")),
    ("build script named", re.compile(r"\bsite/build\.py\b")),
]
STATUS_WORDS = [
    ("coming soon", re.compile(r"\bComing soon\b", re.I)),
    ("placeholder", re.compile(r"\b(?:TODO|TBD|FIXME)\b|lorem ipsum|\[object Object\]")),
]
DOUBLED = re.compile(r"\b([A-Za-z]{3,})\s+\1\b")  # run per text node: table cells like "Yes | Yes" are not bugs
COPY_BUGS = [
    ("visible HTML entity", re.compile(r"&(?:amp|middot|mdash|ndash|rarr|larr|nbsp|quot|#\d+);")),
    ("mojibake", re.compile(r"Ã.|â€|Â ")),
]
SPELLING = [
    ("behavior/behaviour", re.compile(r"\bbehavior", re.I), re.compile(r"\bbehaviour", re.I)),
    ("optimiz/optimis", re.compile(r"\boptimiz", re.I), re.compile(r"\boptimis", re.I)),
    ("organiz/organis", re.compile(r"\borganiz", re.I), re.compile(r"\borganis", re.I)),
    ("analyz/analys", re.compile(r"\banalyz", re.I), re.compile(r"\banalys(?:e|ed|es|ing)\b", re.I)),
    ("labeled/labelled", re.compile(r"\blabeled\b", re.I), re.compile(r"\blabelled\b", re.I)),
    ("program/programme", re.compile(r"\bprogram\b(?!m)", re.I), re.compile(r"\bprogramme\b", re.I)),
]
HOUSE = [
    ("Key Takeaways", re.compile(r"\bKey Takeaways\b", re.I)),
    ("Check Yourself", re.compile(r"\bCheck Yourself\b", re.I)),
    ("References", re.compile(r"\bReferences\b")),
    ("worked example", re.compile(r"\bworked example\b", re.I)),
]
READ_TIME = re.compile(r"\b(\d+)\s*min(?:ute)?s?(?:\s+read)?\b", re.I)
UPDATED = re.compile(r"\b(?:Last updated|Updated|Last reviewed)\b[^.\n]{0,25}\d", re.I)
AUTHOR = re.compile(r"\b(?:Written by|Maintained by|Author:)\s+[A-Z][a-z]+")
EDIT_LINK = re.compile(r"github\.com/[^\"' ]+/(?:blob|edit)/[^\"' ]+/docs/|/issues", re.I)
FEEDBACK_TEXT = re.compile(r"edit (?:this|on github)|suggest (?:an? )?edit|report (?:an? )?(?:issue|error)|feedback", re.I)
REPO_COURSES = re.compile(r"github\.com/[^\"' ]+/(?:blob|tree)/[^\"' ]+/(?:courses|labs)/|\.ipynb\b", re.I)
ANALYTICS = re.compile(r"googletagmanager|google-analytics|plausible|_vercel/insights|vercel-insights|va\.vercel-scripts|posthog|umami|fathom|simpleanalytics|cloudflareinsights", re.I)
CDN_URL = re.compile(r"https://(?:cdn\.jsdelivr\.net/npm|unpkg\.com|cdnjs\.cloudflare\.com/ajax/libs)/[^\"'\s)]+")
PINNED = re.compile(r"@\d+\.\d+\.\d+|/\d+\.\d+\.\d+/")
COUNT_CLAIM = re.compile(
    r"\b(\d{1,3}|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
    r"(?:[a-z-]+\s+)?(questions?|cases|levels|labs|stages|gotchas|TODOs|sections|notebooks|items|modules|courses|chapters|appendices)\b",
    re.I)
TOPICS = {
    "retrieval": re.compile(r"contextual (?:precision|recall)|recall@|precision@|\bMRR\b|\bnDCG\b", re.I),
    "generation": re.compile(r"faithfulness|groundedness|answer relevancy", re.I),
    "tool use": re.compile(r"tool correctness|tool[- ]call|argument correctness", re.I),
    "trajectory": re.compile(r"trajector", re.I),
    "multi-turn": re.compile(r"multi[- ]turn|conversation (?:completeness|relevancy)|knowledge retention", re.I),
    "LLM judges": re.compile(r"LLM[- ]as[- ](?:a[- ])?judge|G-?Eval|judge model", re.I),
    "human labels": re.compile(r"inter[- ]annotator|Cohen'?s kappa|human label|annotat", re.I),
    "statistics": re.compile(r"confidence interval|bootstrap|stratif|statistical significance", re.I),
    "release gate / CI": re.compile(r"release gate|quality gate|regression gate|\bCI\b", re.I),
    "online evaluation": re.compile(r"online evaluation|production monitoring|\bdrift\b", re.I),
    "safety": re.compile(r"red[- ]team|jailbreak|prompt injection|adversarial", re.I),
}
FRAMEWORKS = {
    "DeepEval": re.compile(r"\bdeepeval\b", re.I),
    "RAGAS": re.compile(r"\bragas\b", re.I),
    "MLflow": re.compile(r"\bmlflow\b", re.I),
    "Phoenix": re.compile(r"\bphoenix\b|\barize\b", re.I),
}
RETIRED_API = [
    ("DeepEval LLMTestCaseParams (4.x uses SingleTurnParams in GEval)", re.compile(r"\bLLMTestCaseParams\b")),
    ("RAGAS 0.1-style metric singletons", re.compile(r"from ragas\.metrics import\s+\(?\s*(?:faithfulness|answer_relevancy|context_precision|context_recall)\b")),
    ("MLflow 2 mlflow.evaluate (3.x GenAI uses mlflow.genai.evaluate)", re.compile(r"(?<!genai)\bmlflow\.evaluate\(")),
]


# ---------------------------------------------------------------- fetching
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT = urllib.request.build_opener(_NoRedirect)


def fetch(url: str, timeout: float = 20, follow: bool = True) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    opener = urllib.request.build_opener() if follow else _NO_REDIRECT
    t0 = time.perf_counter()
    try:
        resp = opener.open(req, timeout=timeout)
        ttfb = (time.perf_counter() - t0) * 1000
        status, final, headers, raw = resp.status, resp.geturl(), resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        ttfb = (time.perf_counter() - t0) * 1000
        status, final, headers = e.code, url, e.headers
        try:
            raw = e.read()
        except Exception:
            raw = b""
    except Exception as e:  # DNS, TLS, timeout, proxy refusal
        return {"url": url, "status": None, "error": f"{type(e).__name__}: {e}"}
    charset = headers.get_content_charset() if hasattr(headers, "get_content_charset") else None
    return {
        "url": url,
        "final_url": final,
        "status": status,
        "ttfb_ms": round(ttfb),
        "headers": {k.lower(): v for k, v in headers.items()} if headers else {},
        "body": raw.decode(charset or "utf-8", errors="replace"),
    }


# ---------------------------------------------------------------- parsing
class PageParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title_parts: list[str] = []
        self.h1s: list[str] = []
        self.meta: dict[str, str] = {}
        self.canonical = None
        self.icons: list[str] = []
        self.scripts: list[str] = []
        self.inline_scripts: list[str] = []
        self.jsonld = 0
        self.anchors: list[dict] = []
        self.ids: set[str] = set()
        self.rendered = False   # site/build.py shell: <header class="bar">
        self.docnav = False
        self.details = Counter()
        self.mermaid = 0
        self.code_blocks: list[str] = []
        self.text: list[str] = []
        self.prose_nodes: list[str] = []  # text nodes outside <pre>, for per-node checks
        self._skip = 0
        self._in_title = False
        self._h1: list[str] | None = None
        self._a: dict | None = None
        self._header_depth = 0
        self._script_inline: list[str] | None = None
        self._code: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if a.get("id"):
            self.ids.add(a["id"])
            if a["id"] == "docnav":
                self.docnav = True
        if "mermaid" in cls.split():
            self.mermaid += 1
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._h1 = []
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key and a.get("content") is not None:
                self.meta[key.lower()] = a["content"]
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if "canonical" in rel:
                self.canonical = a.get("href")
            if "icon" in rel:
                self.icons.append(a.get("href") or "")
        elif tag == "script":
            if a.get("type") == "application/ld+json":
                self.jsonld += 1
            if a.get("src"):
                self.scripts.append(a["src"])
            else:
                self._script_inline = []
        elif tag == "header":
            if "bar" in cls.split():
                self.rendered = True
            self._header_depth += 1
        elif tag == "details":
            self.details[cls or "-"] += 1
        elif tag == "pre":
            self._code = []
        elif tag == "a":
            self._a = {"href": a.get("href") or "", "text": [], "in_header": self._header_depth > 0,
                       "label": a.get("aria-label") or "", "class": cls}
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1 is not None:
            self.h1s.append(" ".join(" ".join(self._h1).split()))
            self._h1 = None
        elif tag == "header" and self._header_depth:
            self._header_depth -= 1
        elif tag == "pre" and self._code is not None:
            self.code_blocks.append("".join(self._code))
            self._code = None
        elif tag == "a" and self._a is not None:
            self._a["text"] = " ".join("".join(self._a["text"]).split())
            self.anchors.append(self._a)
            self._a = None
        elif tag == "script" and self._script_inline is not None:
            self.inline_scripts.append("".join(self._script_inline)[:8000])
            self._script_inline = None

    def handle_data(self, data):
        if self._script_inline is not None:
            self._script_inline.append(data)
        if self._in_title:
            self.title_parts.append(data)
        if self._skip:
            return
        if self._h1 is not None:
            self._h1.append(data)
        if self._a is not None:
            self._a["text"].append(data)
        if self._code is not None:
            self._code.append(data)
        else:
            self.prose_nodes.append(data)
        self.text.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self.text).split())


def norm_path(url: str) -> str:
    p = urlparse(url).path or "/"
    if p == "/index.html":
        return "/"
    return p if p == "/" else p.rstrip("/")


def page_kind(path: str, title: str, rendered: bool) -> str:
    if path in HOME_PATHS:
        return "home"
    if EXPLAINER_TITLE.match(title):
        return "explainer"
    if LAB_PATH.match(path) and not rendered:
        return "lab"
    return "doc" if rendered else "standalone"


def samples(regex: re.Pattern, text: str, n: int = 3, width: int = 50) -> list[str]:
    out = []
    for m in regex.finditer(text):
        s, e = max(0, m.start() - width), min(len(text), m.end() + width)
        out.append(text[s:e].strip())
        if len(out) >= n:
            break
    return out


def analyse_page(res: dict) -> dict:
    """Returns the page record; the set of element ids rides along as page['_ids']
    (dropped before writing the inventory) for #fragment checks."""
    page = {k: res.get(k) for k in ("url", "final_url", "status", "ttfb_ms", "error")}
    path = norm_path(res["url"])
    page["path"] = path
    if not res.get("body") or (res.get("status") or 0) >= 400:
        page["kind"] = "error"
        return page
    p = PageParser()
    try:
        p.feed(res["body"])
    except Exception as e:  # malformed HTML should not stop the crawl
        page["parse_error"] = str(e)
    text = p.visible_text
    code = "\n".join(p.code_blocks)
    scripts_blob = " ".join(p.scripts) + " " + " ".join(p.inline_scripts)
    page.update({
        "kind": page_kind(path, p.title, p.rendered),
        "rendered": p.rendered,
        "title": p.title,
        "h1": p.h1s,
        "words": len(re.findall(r"\b\w+\b", text)),
        "lang": p.lang,
        "favicon": bool(p.icons),
        "description": p.meta.get("description") or p.meta.get("og:description"),
        "canonical": p.canonical,
        "og_title": p.meta.get("og:title"),
        "og_image": p.meta.get("og:image"),
        "twitter_card": p.meta.get("twitter:card"),
        "jsonld": p.jsonld,
        "docnav": p.docnav,
        "details": dict(p.details),
        "mermaid": p.mermaid,
        "header_links": [{"href": a["href"], "text": a["text"] or a["label"]} for a in p.anchors if a["in_header"]],
        "links": [{"href": a["href"], "text": a["text"] or a["label"], "class": a["class"]}
                  for a in p.anchors if a["href"]],
        "analytics": bool(ANALYTICS.search(scripts_blob)),
        "cdn_scripts": sorted(set(CDN_URL.findall(scripts_blob))),
        "edit_link": any(EDIT_LINK.search(a["href"]) or FEEDBACK_TEXT.search(a["text"] or a["label"]) for a in p.anchors),
        "repo_code_links": len({a["href"] for a in p.anchors if REPO_COURSES.search(a["href"])}) + len(REPO_COURSES.findall(text)),
    })
    hits = {}
    for name, rx in LEAK:
        s = samples(rx, text)
        if s:
            hits[f"leak: {name}"] = s
    s = samples(DOUBLED, " \u00a6 ".join(p.prose_nodes))
    if s:
        hits["copy: doubled word"] = s
    for name, rx in COPY_BUGS:
        s = samples(rx, text)
        if s:
            hits[f"copy: {name}"] = s
    for name, rx in RETIRED_API:
        s = samples(rx, text)
        if s:
            hits[f"api: {name}"] = s
    page["hits"] = hits
    page["status_words"] = {name: len(rx.findall(text)) for name, rx in STATUS_WORDS if rx.search(text)}
    page["spelling"] = {name: [len(a.findall(text)), len(b.findall(text))] for name, a, b in SPELLING}
    page["house"] = [name for name, rx in HOUSE if rx.search(text)]
    page["read_time"] = bool(READ_TIME.search(text[:3000]))
    page["updated_date"] = bool(UPDATED.search(text))
    page["author_line"] = bool(AUTHOR.search(text))
    page["topics"] = [t for t, rx in TOPICS.items() if len(rx.findall(text)) >= 2]
    page["frameworks"] = {f: [len(rx.findall(text)), len(rx.findall(code))] for f, rx in FRAMEWORKS.items() if rx.search(text)}
    claims = []
    for m in COUNT_CLAIM.finditer(text):
        c = " ".join(m.group(0).split())
        if c not in claims:
            claims.append(c)
    page["count_claims"] = claims[:25]
    page["_ids"] = p.ids
    return page


# ---------------------------------------------------------------- crawl
def read_sitemap(base: str) -> tuple[list[str], dict]:
    """Read /sitemap.xml, following a sitemap index one level down if there is one."""
    res = fetch(urljoin(base, "/sitemap.xml"))
    info = {"status": res.get("status"), "error": res.get("error"), "count": 0, "lastmod": 0, "children": []}
    if res.get("status") != 200:
        return [], info
    bodies = [res["body"]]
    if "<sitemapindex" in res["body"]:
        for child in re.findall(r"<loc>(.*?)</loc>", res["body"], re.S):
            c = fetch(rebase(child.strip(), base))
            info["children"].append({"url": child.strip(), "status": c.get("status")})
            if c.get("status") == 200:
                bodies.append(c["body"])
        bodies = bodies[1:]
    locs = []
    for body in bodies:
        locs += [m.strip() for m in re.findall(r"<url>\s*<loc>(.*?)</loc>", body, re.S)]
        info["lastmod"] += len(re.findall(r"<url>(?:(?!</url>).)*<lastmod>", body, re.S))
    info["count"] = len(locs)
    return locs, info


def rebase(url: str, base: str) -> str:
    b = urlparse(base)
    u = urlparse(url)
    return u._replace(scheme=b.scheme, netloc=b.netloc).geturl()


def internal(href: str, page_url: str, host: str) -> tuple[str, str] | None:
    """(path, fragment) for an internal page link, else None (external, mailto, asset)."""
    if href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    u = urlparse(urljoin(page_url, href))
    if u.netloc != host or not PAGE_EXT.search(u.path or "/"):
        return None
    return norm_path(u.geturl()), u.fragment


def crawl(base: str, seeds: list[str], limit: int | None, workers: int, delay: float) -> tuple[list[dict], dict]:
    """Breadth-first crawl over internal links. Returns (pages, referrers) where
    referrers maps each linked path to the pages that link to it."""
    host = urlparse(base).netloc
    seen = {norm_path(u) for u in seeds}
    frontier = sorted(seen)
    pages, referrers = [], defaultdict(set)

    def one(path):
        time.sleep(delay * random.random())
        return analyse_page(fetch(base + path))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        while frontier:
            if limit:
                frontier = frontier[: max(0, limit - len(pages))]
            batch = list(ex.map(one, frontier))
            pages += batch
            nxt = []
            for pg in batch:
                for ln in pg.get("links", []):
                    hit = internal(ln["href"], pg.get("final_url") or pg["url"], host)
                    if not hit:
                        continue
                    referrers[hit[0]].add(pg["path"])
                    if hit[0] not in seen:
                        seen.add(hit[0])
                        nxt.append(hit[0])
            frontier = sorted(nxt)
            if limit and len(pages) >= limit:
                break
    return pages, referrers


def site_facts(base: str, old_host: str | None = None) -> dict:
    facts = {}
    if old_host and old_host != urlparse(base).netloc:
        t = trace(f"https://{old_host}/")
        facts["old_host"] = {"host": old_host, "final_url": t["final_url"], "final_status": t["final_status"],
                             "hops": [h["status"] for h in t["hops"]],
                             "redirects_to_base": urlparse(t["final_url"]).netloc == urlparse(base).netloc,
                             "permanent": bool(t["hops"]) and all(h["status"] in (301, 308) for h in t["hops"])}
    home = fetch(base + "/")
    facts["home_status"] = home.get("status")
    facts["home_error"] = home.get("error")
    hdr = home.get("headers", {})
    csp = hdr.get("content-security-policy", "")
    facts["security_headers"] = {
        "framing_blocked": bool(hdr.get("x-frame-options")) or "frame-ancestors" in csp,
        "hsts": bool(hdr.get("strict-transport-security")),
        "x_content_type_options": bool(hdr.get("x-content-type-options")),
        "csp": bool(csp),
    }
    robots = fetch(urljoin(base, "/robots.txt"))
    facts["robots"] = {"status": robots.get("status"),
                       "names_sitemap": bool(re.search(r"(?im)^sitemap:", robots.get("body") or ""))}
    facts["pages"] = {}
    for path in ("/about", "/about.html", "/changelog", "/changelog.html"):
        facts["pages"][path] = fetch(urljoin(base, path)).get("status")
    junk = "/" + "".join(random.Random().choices(string.ascii_lowercase, k=12)) + "-audit-404-probe.html"
    nf = fetch(urljoin(base, junk))
    nfp = analyse_page({**nf, "status": 200}) if nf.get("body") else {}
    facts["not_found"] = {"probe": junk, "status": nf.get("status"), "title": nfp.get("title"),
                          "h1": nfp.get("h1"), "hrefs": [l["href"] for l in nfp.get("links", [])]}
    return facts


# ---------------------------------------------------------------- suggestions
def pct(n: int, d: int) -> str:
    return f"{round(100 * n / d)}%" if d else "-"


def words_of(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in {"the", "and", "level"}}


def suggest(base: str, pages: list[dict], referrers: dict, facts: dict, sitemap: dict, sitemap_paths: set,
            sampled: bool = False) -> dict:
    host = urlparse(base).netloc
    ok = [p for p in pages if p.get("status") == 200 and "title" in p]
    by_path = {p["path"]: p for p in ok}
    home = by_path.get("/", {})
    kinds = defaultdict(list)
    for p in ok:
        kinds[p["kind"]].append(p)
    explainers = sorted(kinds["explainer"], key=lambda p: p["path"])
    labs = sorted(kinds["lab"], key=lambda p: p["path"])
    reading = [p for p in ok if p["kind"] in ("explainer", "doc", "standalone")]
    content = [p for p in ok if p["kind"] != "home"]
    s: dict[str, dict] = {}

    def put(cid, status, evidence, details=None):
        s[cid] = {"suggested_status": status, "evidence": evidence, "details": details or []}

    def resolved(p, href):
        return internal(href, p.get("final_url") or p["url"], host)

    # --- IA
    nav = []
    for a in home.get("header_links", []):
        href, text = a["href"], a["text"].strip()
        if not text or href in ("/", "#", "", "index.html") or href.startswith("#"):
            continue
        if text not in [n["text"] for n in nav]:
            nav.append({"text": text, "href": href})
    put("IA-01", "pass" if 0 < len(nav) <= 6 else ("fail" if nav else "not_checked"),
        f"{len(nav)} top-nav items: " + ", ".join(n["text"] for n in nav), nav)

    from_home = {h[0] for l in home.get("links", []) if (h := resolved(home, l["href"]))}
    orphans = [p["path"] for p in content if p["path"] not in from_home]
    put("IA-02", "pass" if not orphans else "fail",
        f"{len(content) - len(orphans)} of {len(content)} pages linked from the index; {len(orphans)} orphans", orphans[:20])

    broken, bad_frag = [], []
    for target, refs in referrers.items():
        tp = by_path.get(target)
        if tp is None:
            st = next((p.get("status") for p in pages if p["path"] == target), "not crawled")
            if st != "not crawled" or not sampled:
                broken.append(f"{target} (HTTP {st}) linked from {', '.join(sorted(refs)[:3])}")
    for p in ok:
        for l in p.get("links", []):
            h = resolved(p, l["href"])
            if h and h[1] and h[0] in by_path and h[1] not in by_path[h[0]].get("_ids", set()):
                bad_frag.append(f"{p['path']} -> {h[0]}#{h[1]}")
    bad_frag = sorted(set(bad_frag))
    put("IA-03", "fail" if broken else ("partial" if bad_frag else "pass"),
        f"{len(broken)} broken internal links, {len(bad_frag)} links to a #fragment that does not exist",
        broken[:15] + bad_frag[:15])

    mism = []
    for l in home.get("links", []):
        h = resolved(home, l["href"])
        tp = by_path.get(h[0]) if h and not h[1] else None
        if not tp or tp["path"] == "/" or not l["text"]:
            continue
        card = words_of(l["text"])
        target = words_of(" ".join(tp.get("h1", [])[:1]))
        if card and len(card & target) / len(card) < 0.5:
            mism.append(f"card '{l['text']}' opens H1 '{(tp.get('h1') or ['-'])[0]}'")
    put("IA-04", "partial" if mism else "pass",
        f"{len(mism)} index cards whose words mostly differ from the page H1 (read to judge)" if mism
        else "Index card titles match their page H1s", sorted(set(mism))[:20])

    seq_gaps = []
    for name, seq in (("explainers", explainers), ("labs", labs)):
        paths = [p["path"] for p in seq]
        for i, p in enumerate(seq):
            linked = {h[0] for l in p.get("links", []) if (h := resolved(p, l["href"]))}
            need = [x for x in (paths[i - 1] if i else None, paths[i + 1] if i + 1 < len(paths) else None) if x]
            miss = [x for x in need if x not in linked]
            if miss:
                seq_gaps.append(f"{p['path']} does not link to {', '.join(miss)}")
    put("IA-05", "pass" if not seq_gaps else ("partial" if len(seq_gaps) < (len(explainers) + len(labs)) / 2 else "fail"),
        f"{len(seq_gaps)} of {len(explainers) + len(labs)} sequence pages ({len(explainers)} explainers, {len(labs)} labs) "
        "miss a prev or next link", seq_gaps[:20])

    badurl = [p["path"] for p in ok if not GOOD_URL.match(p["path"])]
    put("IA-08", "pass" if not badurl else "fail",
        f"{len(badurl)} page URLs outside the /<lowercase-kebab>.html pattern", badurl[:15])

    # --- ON
    repo = [l["href"] for l in home.get("links", []) if "github.com" in l["href"]]
    put("ON-06", "partial" if repo else "fail",
        f"Index links to the repository ({repo[0]}); read whether it names the course and setup" if repo
        else "Index has no link to the repository")

    # --- FV
    found = []
    for p in [home] + [p for p in ok if p["kind"] in ("doc", "standalone")]:
        if p and p.get("count_claims"):
            found.append(f"{p['path']}: " + ", ".join(p["count_claims"][:10]))
    facts_seen = [f"explainers published: {len(explainers)}", f"labs published: {len(labs)}"]
    for p in ok:
        qa = p.get("details", {}).get("qa")
        if qa:
            facts_seen.append(f"{p['path']}: {qa} collapsible Q&A items")
    put("FV-04", "not_checked",
        "Counts claimed on the index and pages are listed below with what the scan counted; compare by reading",
        facts_seen + found[:20])

    stubs = [f"{p['path']} ({p['words']} words)" for p in reading if p.get("words", 999) < 300]
    ph = [f"{p['path']}: " + ", ".join(f"{k} x{v}" for k, v in p["status_words"].items()) for p in ok if p.get("status_words")]
    put("FV-05", "fail" if stubs or ph else "pass",
        f"{len(stubs)} reading pages under 300 served words (a page drawn by JavaScript looks short here: confirm in the "
        f"browser); {len(ph)} pages with placeholder or Coming soon text (may be content, e.g. 'TODOs': read)", stubs[:10] + ph[:10])

    home_leaks = [k for k in home.get("hits", {}) if k.startswith("leak")]
    put("FV-06", "fail" if home_leaks else "pass",
        ("Index shows build internals: " + "; ".join(f"{k} …{home['hits'][k][0]}…" for k in home_leaks)) if home_leaks
        else "No build internals found on the index")

    # --- PQ
    nav_targets = {h for n in nav if (h := resolved(home, n["href"]))}
    no_shell = []
    for p in content:
        have = {h for l in p.get("links", []) if (h := resolved(p, l["href"]))}
        home_link = any(h[0] == "/" for h in have)
        if not home_link or (nav_targets and len(nav_targets & have) < len(nav_targets)):
            no_shell.append(f"{p['path']} ({p['kind']}): home link {'yes' if home_link else 'no'}, "
                            f"{len(nav_targets & have)}/{len(nav_targets)} nav sections")
    put("PQ-01", "pass" if not no_shell else ("partial" if len(no_shell) < len(content) / 2 else "fail"),
        f"{len(no_shell)} of {len(content)} pages lack the index link or some top-nav sections", no_shell[:15])

    timed = [p for p in reading if p.get("read_time")]
    put("PQ-03", "pass" if reading and len(timed) == len(reading) else ("partial" if timed else "fail"),
        f"Reading time in served text on {len(timed)} of {len(reading)} reading pages (may be drawn by JavaScript: confirm in the browser)",
        [p["path"] for p in reading if not p.get("read_time")][:15])

    long_bare = [f"{p['path']} ({p['words']} words)" for p in ok
                 if p.get("words", 0) > 2000 and not p.get("docnav") and sum(p.get("details", {}).values()) < 4]
    put("PQ-04", "pass" if not long_bare else "fail",
        f"{len(long_bare)} pages over 2,000 words with no contents rail or collapsible sections", long_bare[:15])

    house_miss = [f"{p['path']}: missing " + ", ".join(n for n, _ in HOUSE if n not in p.get("house", []))
                  for p in explainers if len(p.get("house", [])) < len(HOUSE)]
    put("PQ-05", "pass" if explainers and not house_miss else ("partial" if explainers else "not_checked"),
        f"{len(explainers) - len(house_miss)} of {len(explainers)} explainers have Key Takeaways, Check Yourself, "
        "References and a worked example (headings still need reading)", house_miss[:15])

    leaks = [(p["path"], k, v[0]) for p in ok for k, v in p.get("hits", {}).items() if k.startswith("leak")]
    put("PQ-06", "fail" if leaks else "pass",
        f"{len(leaks)} build-artefact hits on {len({l[0] for l in leaks})} pages",
        [f"{a} [{b}] …{c}…" for a, b, c in leaks[:20]])

    copy = [(p["path"], k, v[0]) for p in ok for k, v in p.get("hits", {}).items() if k.startswith("copy")]
    put("PQ-07", "fail" if copy else "partial",
        f"{len(copy)} copy-bug hits (doubled words can be legitimate, e.g. code; read each)" if copy
        else "No pattern hits; contradictions (e.g. 'six' listing seven) need reading",
        [f"{a} [{b}] …{c}…" for a, b, c in copy[:20]])

    spell = []
    for name, _, _ in SPELLING:
        us = sum(p.get("spelling", {}).get(name, [0, 0])[0] for p in ok)
        uk = sum(p.get("spelling", {}).get(name, [0, 0])[1] for p in ok)
        if us and uk:
            spell.append(f"{name}: US {us}, UK {uk}")
    put("PQ-08", "fail" if spell else "pass", "; ".join(spell) if spell else "One spelling system in use", spell)

    dated = sum(1 for p in reading if p.get("updated_date"))
    authored = sum(1 for p in reading if p.get("author_line"))
    put("PQ-10", ("pass" if dated == authored == len(reading) else "partial" if dated or authored else "fail")
        if reading else "not_checked",
        f"Last-updated date on {pct(dated, len(reading))}, author line on {pct(authored, len(reading))} of {len(reading)} reading pages")

    # --- PR
    hostname = urlparse(base).netloc
    oh = facts.get("old_host")
    if hostname.endswith("vercel.app"):
        put("PR-01", "fail", f"Served from {hostname}")
    elif oh and oh["redirects_to_base"] and oh["permanent"]:
        put("PR-01", "pass", f"Served from {hostname}; {oh['host']} permanently redirects here")
    elif oh:
        put("PR-01", "partial", f"Served from {hostname}, but {oh['host']} ends at {oh['final_url']} "
                                f"(HTTP {oh['final_status']}, hops {oh['hops']}); it should 301 to {hostname}")
    else:
        put("PR-01", "pass", f"Served from {hostname}")

    og = sum(1 for p in ok if p.get("og_image"))
    card = home.get("twitter_card")
    put("PR-02", "pass" if og == len(ok) and card == "summary_large_image" else ("partial" if og else "fail"),
        f"og:image on {og} of {len(ok)} pages; og:title on {sum(1 for p in ok if p.get('og_title'))}; "
        f"index twitter:card = {card!r}")

    canon = [p for p in ok if p.get("canonical")]
    put("PR-03", "pass" if len(canon) == len(ok) else ("partial" if canon else "fail"),
        f"canonical tag on {len(canon)} of {len(ok)} pages")

    put("PR-04", "pass" if home.get("analytics") else "not_checked",
        "Analytics script found in served HTML" if home.get("analytics")
        else "None in served HTML; confirm in the browser (may load client-side)")

    ex = facts.get("pages", {})
    about = next((p for p in ("/about", "/about.html") if ex.get(p) == 200 or p in by_path), None)
    put("PR-05", "partial" if about else "fail",
        f"{about} exists; read it for maintainer, background and contact" if about
        else "/about and /about.html return " + ", ".join(str(ex.get(p)) for p in ("/about", "/about.html"))
        + "; read the index for an author section before failing")

    fb = sum(1 for p in content if p.get("edit_link"))
    put("PR-06", "pass" if content and fb == len(content) else ("partial" if fb else "fail"),
        f"Edit-on-GitHub, issue or feedback link on {fb} of {len(content)} pages")

    nf = facts.get("not_found", {})
    nf_nav = sum(1 for h in nf.get("hrefs", []) if "index.html" in h or h == "/")
    put("PR-07", "pass" if nf.get("status") == 404 and nf_nav else "fail",
        f"Probe {nf.get('probe')} -> HTTP {nf.get('status')}, title {nf.get('title')!r}, "
        f"{nf_nav} links back to the index")

    rb = facts.get("robots", {})
    put("PR-08", "pass" if rb.get("status") == 200 and rb.get("names_sitemap") and sitemap.get("status") == 200 else "fail",
        f"robots.txt HTTP {rb.get('status')} (names sitemap: {rb.get('names_sitemap')}); "
        f"sitemap.xml HTTP {sitemap.get('status')}, {sitemap.get('count')} URLs")

    if not sitemap.get("count"):
        put("PR-09", "na", "No sitemap; PR-08 carries the finding")
    else:
        crawled = {p["path"] for p in ok}
        missing, extra = sorted(crawled - sitemap_paths), sorted(sitemap_paths - crawled)
        put("PR-09", "pass" if not missing and not extra and sitemap.get("lastmod") == sitemap.get("count") else "fail",
            f"{len(missing)} crawled pages missing from the sitemap, {len(extra)} sitemap URLs not reachable by links; "
            f"lastmod on {sitemap.get('lastmod')} of {sitemap.get('count')}", (missing + extra)[:15])

    one_h1 = sum(1 for p in ok if len(p.get("h1", [])) == 1)
    lang = sum(1 for p in ok if p.get("lang"))
    fav = sum(1 for p in ok if p.get("favicon"))
    desc = sum(1 for p in ok if p.get("description"))
    put("PR-10", "pass" if one_h1 == lang == fav == desc == len(ok) else ("partial" if one_h1 + lang + fav + desc else "fail"),
        f"One H1 on {one_h1}, lang on {lang}, favicon on {fav}, meta description on {desc} of {len(ok)} pages",
        [f"{p['path']}: {len(p.get('h1', []))} H1s" for p in ok if len(p.get("h1", [])) != 1][:10]
        + [f"{p['path']}: no favicon" for p in ok if not p.get("favicon")][:5])

    ttfb = [p["ttfb_ms"] for p in ok if p.get("ttfb_ms") is not None]
    med = round(statistics.median(ttfb)) if ttfb else None
    # Concurrent crawl timings from this machine are information only; B7 decides.
    put("PR-12", "not_checked",
        f"Crawl median time to first byte {med} ms over {len(ttfb)} pages (concurrent, from this machine; "
        "information only, decide with browser check B7)" if med is not None else "No timings")

    jl = sum(1 for p in ok if p.get("jsonld"))
    put("PR-13", "pass" if jl == len(ok) else ("partial" if jl else "fail"), f"JSON-LD on {jl} of {len(ok)} pages")

    changelog = next((p for p in ("/changelog", "/changelog.html") if ex.get(p) == 200 or p in by_path), None)
    put("PR-15", "pass" if changelog or home.get("updated_date") else "fail",
        f"{changelog} exists" if changelog else ("Index shows a last-updated date" if home.get("updated_date")
                                                 else "No /changelog and no last-updated date on the index"))

    sh = facts.get("security_headers", {})
    good = sum(1 for v in sh.values() if v)
    put("PR-18", "pass" if good == 4 else ("partial" if good else "fail"),
        ", ".join(f"{k}: {'yes' if v else 'no'}" for k, v in sh.items()))

    cdn = sorted({u for p in ok for u in p.get("cdn_scripts", [])})
    loose = [u for u in cdn if not PINNED.search(u)]
    put("PR-19", "pass" if not loose else "fail",
        f"{len(loose)} of {len(cdn)} CDN script URLs not pinned to an exact version", loose[:10])

    # --- CT
    topic_pages = {t: [p["path"] for p in ok if t in p.get("topics", [])] for t in TOPICS}
    thin = [t for t, v in topic_pages.items() if len(v) < 2]
    put("CT-01", "partial" if not thin else "fail",
        (f"Every topic recurs on 2+ pages; read to judge depth" if not thin
         else f"Topics on fewer than 2 pages: {', '.join(thin)}"),
        [f"{t}: {len(v)} pages" for t, v in topic_pages.items()])

    put("CT-03", ("pass" if all(p.get("repo_code_links") for p in explainers) else
                  "partial" if any(p.get("repo_code_links") for p in explainers) else "fail") if explainers else "not_checked",
        f"{sum(1 for p in explainers if p.get('repo_code_links'))} of {len(explainers)} explainers link to a notebook "
        "or course folder in the repo (lab links count too: read)",
        [p["path"] for p in explainers if not p.get("repo_code_links")][:15])

    fw = {f: [0, 0, 0] for f in FRAMEWORKS}  # pages mentioning, total mentions, mentions inside code
    for p in ok:
        for f, (n, c) in p.get("frameworks", {}).items():
            fw[f][0] += 1
            fw[f][1] += n
            fw[f][2] += c
    no_code = [f for f, v in fw.items() if not v[2]]
    put("CT-04", "partial" if not no_code else "fail",
        "; ".join(f"{f}: {v[0]} pages, {v[2]} mentions in code" for f, v in fw.items())
        + (f". No code shown for {', '.join(no_code)}" if no_code else ""))

    api = [(p["path"], k, v[0]) for p in ok for k, v in p.get("hits", {}).items() if k.startswith("api")]
    put("CT-10", "partial" if api else "pass",
        f"{len(api)} retired-API hits (read context: a page may name the old API to warn against it)" if api
        else "No retired DeepEval / RAGAS / MLflow API names found",
        [f"{a} [{b}] …{c}…" for a, b, c in api[:15]])

    worked = [p for p in explainers + kinds["doc"] if "worked example" in p.get("house", [])]
    pool = explainers + kinds["doc"]
    put("CT-07", ("pass" if len(worked) == len(pool) else "partial" if worked else "fail") if pool else "not_checked",
        f"'Worked example' on {len(worked)} of {len(pool)} explainer and theory pages (read for concrete numbers)",
        [p["path"] for p in pool if p not in worked][:15])

    hidden = [p for p in explainers if "Check Yourself" in p.get("house", [])
              and sum(v for k, v in p.get("details", {}).items() if k != "refs") > 0]
    with_cy = [p for p in explainers if "Check Yourself" in p.get("house", [])]
    put("CT-09", ("pass" if len(hidden) == len(explainers) else "partial" if with_cy else "fail") if explainers else "not_checked",
        f"Check Yourself on {len(with_cy)} of {len(explainers)} explainers; answers hidden (collapsible) on {len(hidden)}")

    if sampled:
        # counts from a sample say nothing about the whole site; never let a
        # sample report the core content as missing
        note = " (sampled crawl: run without --limit to decide)"
        put("CT-02", "not_checked", f"{len(explainers)} explainers in the sample" + note)
        put("CT-05", "not_checked", f"{len(labs)} labs in the sample" + note)
    else:
        levels = sorted(int(m.group(1)) for p in explainers if (m := EXPLAINER_TITLE.match(p["title"])))
        missing = [n for n in range(11) if n not in levels]
        put("CT-02", "pass" if not missing else "fail",
            f"{len(explainers)} explainers, levels {levels}" + (f"; missing {missing}" if missing else ""))
        put("CT-05", "pass" if len(labs) >= 6 else "fail",
            f"{len(labs)} interactive lab pages: " + ", ".join(p["path"] for p in labs))
    return s


# ---------------------------------------------------------------- legacy redirects
REDIRECT_CODES = (301, 302, 303, 307, 308)


def trace(url: str, max_hops: int = 6) -> dict:
    """Follow redirects by hand, recording each hop, so we can tell a moved page
    from a mere host or trailing-slash hop."""
    start = norm_path(url)
    hops, current = [], url
    for _ in range(max_hops):
        r = fetch(current, follow=False)
        loc = (r.get("headers") or {}).get("location")
        if r.get("status") in REDIRECT_CODES and loc:
            nxt = urljoin(current, loc)
            hops.append({"status": r["status"], "to": nxt, "path_changed": norm_path(nxt) != norm_path(current)})
            current = nxt
            continue
        return {"final_url": current, "final_status": r.get("status"), "error": r.get("error"), "hops": hops,
                "moved": norm_path(current) != start}
    return {"final_url": current, "final_status": None, "error": "too many redirects", "hops": hops,
            "moved": norm_path(current) != start}


def check_legacy(base: str, legacy_file: Path, workers: int) -> dict:
    """IA-09: every retired URL should permanently redirect to a live page that is not the index."""
    paths = [l.strip() for l in legacy_file.read_text().splitlines() if l.strip() and not l.startswith("#")]

    def one(path):
        t = trace(urljoin(base, path))
        moving = [h for h in t["hops"] if h["path_changed"]]
        if t["final_status"] != 200:
            kind = "broken"
        elif t["moved"] and norm_path(t["final_url"]) == "/":
            kind = "sent to home"
        elif t["moved"] and any(h["status"] not in (301, 308) for h in moving):
            kind = "temporary redirect"
        elif t["moved"]:
            kind = "permanent redirect"
        else:
            kind = "still live"
        return {"path": path, "kind": kind, **t}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, paths))
    c = Counter(r["kind"] for r in results)
    bad = [r for r in results if r["kind"] in ("broken", "sent to home")]
    if bad:
        status = "fail"
    elif c["temporary redirect"] or (c["still live"] and c["permanent redirect"]):
        status = "partial"
    elif c["permanent redirect"]:
        status = "pass"
    else:
        status = "na"  # nothing retired yet
    return {
        "suggestion": {
            "suggested_status": status,
            "evidence": f"{len(paths)} retired URLs: " + ", ".join(f"{k} {v}" for k, v in c.most_common()),
            "details": [f"{r['path']} -> {r['kind']} ({r['final_status']}) {r['final_url']}"
                        for r in (bad + [r for r in results if r["kind"] in ("temporary redirect", "still live")])][:25],
        },
        "results": results,
    }


# ---------------------------------------------------------------- output
def write_summary(out: Path, base: str, pages: list[dict], facts: dict, sitemap: dict, sugg: dict,
                  catalog: dict | None, sampled: bool) -> None:
    titles = {c["id"]: c["title"] for c in (catalog or {}).get("checks", [])}
    ok = [p for p in pages if p.get("status") == 200]
    errs = [p for p in pages if p.get("status") != 200]
    kinds = Counter(p.get("kind") for p in ok)
    L = [f"# Scan summary — {time.strftime('%Y-%m-%d')}", "", f"Base: {base}  ",
         f"Sitemap: HTTP {sitemap.get('status')}, {sitemap.get('count')} URLs. "
         f"Crawled {len(pages)} pages by following links: {len(ok)} OK, {len(errs)} not OK.  ",
         "Pages by kind: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()), ""]
    if sampled:
        L += ["**Sampled crawl** (--limit): good for a quick look, not for a recorded audit. "
              "Counts and percentages below cover the sample only.", ""]
    if errs:
        L += ["## Pages not returning 200", ""] + [f"- {p['path']}: {p.get('status')} {p.get('error') or ''}" for p in errs[:30]] + [""]
    L += ["## Suggested check results", "", "These are suggestions from served HTML. Confirm before recording them.", "",
          "| Check | Title | Suggested | Evidence |", "| --- | --- | --- | --- |"]
    for cid in sorted(sugg):
        v = sugg[cid]
        L.append(f"| {cid} | {titles.get(cid, '')} | {v['suggested_status']} | {v['evidence'].replace('|', '/')} |")
    L.append("")
    for cid in sorted(sugg):
        d = sugg[cid].get("details")
        if d:
            L += [f"### {cid} details", ""] + [f"- {x if isinstance(x, str) else json.dumps(x)}" for x in d] + [""]
    out.joinpath("scan-summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="site root, e.g. https://eval-demystified.vercel.app (a page URL is cut to its root)")
    ap.add_argument("--out", required=True, help="audit folder, e.g. .website_spec/site-audits/2026-10-14")
    ap.add_argument("--limit", type=int, help="crawl at most N pages (breadth first from the index)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--delay", type=float, default=0.3, help="max random delay per request, seconds")
    ap.add_argument("--legacy", help="file of retired paths to test for permanent redirects (IA-09)")
    ap.add_argument("--old-host", help="previous host; after a domain move PR-01 checks it permanently redirects to --base")
    ap.add_argument("--catalog", default=str(Path(__file__).resolve().parent.parent / "data" / "checks.json"))
    args = ap.parse_args(argv)

    u = urlparse(args.base)
    base = f"{u.scheme}://{u.netloc}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(Path(args.catalog).read_text()) if Path(args.catalog).exists() else None

    facts = site_facts(base, args.old_host)
    if facts.get("home_status") != 200:
        why = facts.get("home_error") or f"index returned HTTP {facts.get('home_status')}"
        print(f"Cannot audit {base}: {why}.", file=sys.stderr)
        if facts.get("home_status") in (401, 403):
            print("This looks like deployment protection or a firewall: use the public production URL.", file=sys.stderr)
        print("If this shell has no internet access, fall back to WebFetch for the index and key pages (see SKILL.md).", file=sys.stderr)
        return 3
    locs, sitemap = read_sitemap(base)
    sitemap_paths = {norm_path(rebase(x, base)) for x in locs}
    print(f"Crawling {base} by following links{' (+ sitemap)' if locs else ''} ...", file=sys.stderr)
    pages, referrers = crawl(base, ["/"] + sorted(sitemap_paths), args.limit, args.workers, args.delay)
    sampled = bool(args.limit) and len(pages) >= args.limit
    ok = sum(1 for p in pages if p.get("status") == 200)
    if ok < max(3, len(pages) // 2):
        for p in pages:
            p.pop("_ids", None)
        out.joinpath("inventory.json").write_text(json.dumps({"base": base, "pages": pages, "site": facts}, indent=1), encoding="utf-8")
        print(f"Only {ok} of {len(pages)} pages returned 200, so the scan would mislead; no suggestions written. "
              f"See {out}/inventory.json for the statuses.", file=sys.stderr)
        return 4
    sugg = suggest(base, pages, referrers, facts, sitemap, sitemap_paths, sampled)

    if args.legacy:
        red = check_legacy(base, Path(args.legacy), args.workers)
        sugg["IA-09"] = red["suggestion"]
        out.joinpath("redirects.json").write_text(json.dumps(red["results"], indent=2), encoding="utf-8")
    else:
        sugg["IA-09"] = {"suggested_status": "na", "evidence": "No --legacy file: no retired URLs to test", "details": []}

    for p in pages:
        p.pop("_ids", None)
    inv = {"base": base, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "sitemap": sitemap,
           "site": facts, "pages": pages,
           "referrers": {k: sorted(v) for k, v in sorted(referrers.items())}}
    out.joinpath("inventory.json").write_text(json.dumps(inv, indent=1, ensure_ascii=False), encoding="utf-8")
    out.joinpath("scan-checks.json").write_text(json.dumps(sugg, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary(out, base, pages, facts, sitemap, sugg, catalog, sampled)
    fails = sum(1 for v in sugg.values() if v["suggested_status"] == "fail")
    print(f"Done: {len(pages)} pages, {len(sugg)} checks suggested ({fails} fail). See {out}/scan-summary.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
