#!/usr/bin/env python3
"""Crawl the Forward Deployed site from its sitemap and run every audit check
that can be decided from served HTML. Standard library only.

Outputs (in --out):
  inventory.json     every page: status, timing, title, H1s, meta, word count,
                     pattern hits; plus site-level facts (robots, sitemap, 404,
                     headers, top nav)
  scan-checks.json   suggested status + evidence per check ID (data/checks.json)
  scan-summary.md    the same, readable, with offending URLs
  redirects.json     only with --legacy: how each retired URL now responds

The scan suggests; it does not decide. Every suggestion is confirmed by reading
pages or in the browser before it goes into scores.json (see the site-audit SKILL.md).

Usage:
  python3 crawl_inventory.py --base https://forwarddeployedprep.com --out .website_spec/site-audits/2026-11-20
  python3 crawl_inventory.py --base URL --out DIR --limit 60          # quick sample
  python3 crawl_inventory.py --base URL --out DIR --legacy data/legacy-urls-2026-10-09.txt   # path relative to this profile folder
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

UA = "site-audit/1.0 (fde profile; site owner audit)"

SCHEMES = [
    ("home", r"^/$"),
    ("start", r"^/start(/|$)"),
    ("learn", r"^/learn(/|$)"),
    ("legacy-modules", r"^/modules/\d{2}-"),
    ("interview", r"^/interview(/|$)"),
    ("final-week-html", r"^/fde-last-day-prep/.*\.html$"),
    ("final-week-legacy", r"^/fde-last-day-prep(/|$)"),
    ("casebook", r"^/(casebook|design)(/|$)"),
    ("practice", r"^/practice(/|$)"),
    ("final-week", r"^/final-week(/|$)"),
    ("company-prep", r"^/company-prep(/|$)"),
    ("utility", r"^/(glossary|library|guide|learning-map|about|changelog|credits)(/|$)"),
    ("other", r".*"),
]
HUB_PATHS = {"/", "/start", "/learn", "/design", "/casebook", "/practice", "/interview",
             "/final-week", "/fde-last-day-prep", "/company-prep", "/library"}
CASEBOOK_ITEM = re.compile(r"^/(modules/15-fde-case-studies/[^/]+/[^/]+|casebook/[^/]+)$")
FINAL_WEEK_ITEM = re.compile(r"^/(fde-last-day-prep/.+\.html|final-week/[^/]+)$")

LEAK = [
    ("source file path", re.compile(r"\b[\w./-]*\w\.(?:md|ipynb|xlsx|csv)\b")),
    ("generated-from footer", re.compile(r"Generated from", re.I)),
    ("repo link as content", re.compile(r"github\.com/\S+\.md", re.I)),
    ("empty tool lead-in", re.compile(r"for a viewer that draws Mermaid", re.I)),
]
STATUS_WORDS = [
    ("coming soon", re.compile(r"\bComing soon\b", re.I)),
    ("on hold", re.compile(r"\bOn hold\b|Paused, will return|\bPaused\b", re.I)),
    ("partly ready", re.compile(r"\bPartly ready\b", re.I)),
    ("blocked", re.compile(r"\bBlocked\b")),
]
COPY_BUGS = [
    ("doubled word", re.compile(r"\b([A-Z][a-z]{2,})\s+\1\b")),
    ("glued number", re.compile(r"[a-z]\d+ (?:modules|lessons|tracks|cases)\b")),
    ("placeholder", re.compile(r"\b(?:TODO|TBD|FIXME)\b|lorem ipsum|\[object Object\]", re.I)),
]
SPELLING = [
    ("behavior/behaviour", re.compile(r"\bbehavior", re.I), re.compile(r"\bbehaviour", re.I)),
    ("authoriz/authoris", re.compile(r"\bauthoriz", re.I), re.compile(r"\bauthoris", re.I)),
    ("optimiz/optimis", re.compile(r"\boptimiz", re.I), re.compile(r"\boptimis", re.I)),
    ("organiz/organis", re.compile(r"\borganiz", re.I), re.compile(r"\borganis", re.I)),
    ("analyz/analys", re.compile(r"\banalyz", re.I), re.compile(r"\banalys(?:e|ed|es|ing)\b", re.I)),
]
OBJECTIVE_LABELS = [
    ("By the end you can", re.compile(r"By the end you can", re.I)),
    ("Objectives:", re.compile(r"\bObjectives:")),
    ("You will be able to", re.compile(r"You will be able to", re.I)),
]
READ_TIME = re.compile(r"(\d+)\s*min(?:ute)?s?\s+read", re.I)
CLOCK_TIME = re.compile(r"[◷⏱🕒]\s*(\d+)\s*min", re.I)
TITLE_CODE = re.compile(
    r"(?:^|[·|—–-]\s*)(G\d{2}|#\d{1,3}(?:[–-]\d{1,3})*|Review\s\d{2}|T\d{1,2}(?:\.\d{1,2})?|I\d)(?=\s*[·|—–-]|\s*$)"
)
LEVEL_CAL = re.compile(r"expected at each level|what (?:a )?(?:senior|staff|principal)|senior[^.\n]{0,60}staff|level calibration", re.I)
UPDATED = re.compile(r"\b(?:Last updated|Updated)\b[^.\n]{0,25}\d", re.I)
AUTHOR = re.compile(r"\b(?:Written by|Author:|By)\s+[A-Z][a-z]+", re.M)
FEEDBACK_LINK = re.compile(r"report (?:an? )?(?:issue|error|problem)|feedback|suggest (?:an? )?edit|edit this page", re.I)
ANALYTICS = re.compile(r"googletagmanager|google-analytics|plausible|_vercel/insights|vercel-insights|va\.vercel-scripts|posthog|umami|fathom|simpleanalytics|cloudflareinsights", re.I)
STUB = re.compile(r"has no lessons yet|is paused while|still being written|Paused, will return", re.I)
DRAWING = re.compile(r"Drawing diagram", re.I)
COUNT_CLAIM = re.compile(
    r"\b(\d{1,3})\s+(?:ready\s+)?(?:curriculum\s+)?(tracks?|modules?|worked system designs|designs|technical worksheets|"
    r"behavioural worksheets|worksheets|final-week reviews|reviews|parts|lessons)\b", re.I)


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
        self.h2 = 0
        self.meta: dict[str, str] = {}
        self.canonical = None
        self.icons: list[str] = []
        self.scripts: list[str] = []
        self.inline_scripts: list[str] = []
        self.jsonld = 0
        self.anchors: list[dict] = []
        self.has_header = False
        self.has_footer = False
        self.text: list[str] = []
        self._skip = 0
        self._in_title = False
        self._h1: list[str] | None = None
        self._a: dict | None = None
        self._header_depth = 0
        self._script_inline: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._h1 = []
        elif tag == "h2":
            self.h2 += 1
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
            self.has_header = True
            self._header_depth += 1
        elif tag == "footer":
            self.has_footer = True
        elif tag == "a":
            self._a = {"href": a.get("href") or "", "text": [], "in_header": self._header_depth > 0,
                       "label": a.get("aria-label") or ""}
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1 is not None:
            self.h1s.append(" ".join("".join(self._h1).split()))
            self._h1 = None
        elif tag == "header" and self._header_depth:
            self._header_depth -= 1
        elif tag == "a" and self._a is not None:
            self._a["text"] = " ".join("".join(self._a["text"]).split())
            self.anchors.append(self._a)
            self._a = None
        elif tag == "script" and self._script_inline is not None:
            self.inline_scripts.append("".join(self._script_inline)[:4000])
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
        self.text.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self.text).split())


def classify(path: str) -> str:
    for name, pat in SCHEMES:
        if re.search(pat, path):
            return name
    return "other"


def norm_path(url: str) -> str:
    p = urlparse(url).path or "/"
    return p if p == "/" else p.rstrip("/")


def samples(regex: re.Pattern, text: str, n: int = 3, width: int = 50) -> list[str]:
    out = []
    for m in regex.finditer(text):
        s, e = max(0, m.start() - width), min(len(text), m.end() + width)
        out.append(text[s:e].strip())
        if len(out) >= n:
            break
    return out


def analyse_page(res: dict) -> dict:
    page = {k: res.get(k) for k in ("url", "final_url", "status", "ttfb_ms", "error")}
    path = norm_path(res["url"])
    page["path"] = path
    page["scheme"] = classify(path)
    if not res.get("body") or (res.get("status") or 0) >= 400:
        return page
    p = PageParser()
    try:
        p.feed(res["body"])
    except Exception as e:  # malformed HTML should not stop the crawl
        page["parse_error"] = str(e)
    text = p.visible_text
    page.update({
        "title": p.title,
        "h1": p.h1s,
        "h2_count": p.h2,
        "words": len(re.findall(r"\b\w+\b", text)),
        "lang": p.lang,
        "favicon": bool(p.icons),
        "canonical": p.canonical,
        "og_image": p.meta.get("og:image"),
        "twitter_card": p.meta.get("twitter:card"),
        "description": p.meta.get("description") or p.meta.get("og:description"),
        "jsonld": p.jsonld,
        "has_header": p.has_header,
        "has_footer": p.has_footer,
        "header_links": [{"href": a["href"], "text": a["text"] or a["label"]} for a in p.anchors if a["in_header"]],
        "hrefs": sorted({a["href"] for a in p.anchors if a["href"]}),
        "analytics": bool(ANALYTICS.search(" ".join(p.scripts) + " " + " ".join(p.inline_scripts))),
        "feedback_link": any(FEEDBACK_LINK.search(a["text"] or a["label"]) for a in p.anchors),
    })
    hits = {}
    for name, rx in LEAK:
        s = samples(rx, text)
        if s:
            hits[f"leak: {name}"] = s
    for name, rx in COPY_BUGS:
        s = samples(rx, text)
        if s:
            hits[f"copy: {name}"] = s
    page["hits"] = hits
    page["status_words"] = {name: len(rx.findall(text)) for name, rx in STATUS_WORDS if rx.search(text)}
    page["spelling"] = {name: [len(a.findall(text)), len(b.findall(text))] for name, a, b in SPELLING}
    page["objective_labels"] = [name for name, rx in OBJECTIVE_LABELS if rx.search(text)]
    page["read_times"] = [int(x) for x in READ_TIME.findall(text)]
    page["clock_times"] = [int(x) for x in CLOCK_TIME.findall(text)]
    page["title_code"] = bool(TITLE_CODE.search(p.title))
    page["h1_code"] = any(TITLE_CODE.search(h) for h in p.h1s)
    page["level_calibration"] = bool(LEVEL_CAL.search(text))
    page["updated_date"] = bool(UPDATED.search(text))
    page["author_line"] = bool(AUTHOR.search(text))
    page["stub"] = bool(STUB.search(text))
    page["drawing_placeholders"] = len(DRAWING.findall(text))
    claims = []
    for m in COUNT_CLAIM.finditer(text):
        c = " ".join(m.group(0).split())
        if c not in claims:
            claims.append(c)
    page["count_claims"] = claims[:20]
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
    info["legacy_entries"] = [u for u in locs if re.search(r"\.html$|/modules/\d{2}-", urlparse(u).path)]
    return locs, info


def rebase(url: str, base: str) -> str:
    b = urlparse(base)
    u = urlparse(url)
    return u._replace(scheme=b.scheme, netloc=b.netloc).geturl()


def choose(urls: list[str], limit: int | None) -> list[str]:
    if not limit or limit >= len(urls):
        return urls
    hubs = [u for u in urls if norm_path(u).count("/") <= 2]
    rest = [u for u in urls if u not in hubs]
    random.Random(7).shuffle(rest)
    by_scheme = defaultdict(list)
    for u in rest:
        by_scheme[classify(norm_path(u))].append(u)
    picked = hubs[:limit]
    while len(picked) < limit and any(by_scheme.values()):
        for k in list(by_scheme):
            if by_scheme[k] and len(picked) < limit:
                picked.append(by_scheme[k].pop())
    return picked


def crawl(base: str, urls: list[str], workers: int, delay: float) -> list[dict]:
    def one(u):
        time.sleep(delay * random.random())
        return analyse_page(fetch(u))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(one, urls))


def site_facts(base: str, old_host: str | None = None) -> dict:
    facts = {}
    if old_host and old_host != urlparse(base).netloc:
        t = trace(f"https://{old_host}/")
        facts["old_host"] = {"host": old_host, "final_url": t["final_url"], "final_status": t["final_status"],
                             "hops": [h["status"] for h in t["hops"]],
                             "redirects_to_base": urlparse(t["final_url"]).netloc == urlparse(base).netloc,
                             "permanent": bool(t["hops"]) and all(h["status"] in (301, 308) for h in t["hops"])}
    home = fetch(base)
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
    for path in ("/about", "/changelog"):
        r = fetch(urljoin(base, path))
        facts["pages"][path] = r.get("status")
    junk = "/" + "".join(random.Random().choices(string.ascii_lowercase, k=12)) + "-audit-404-probe"
    nf = fetch(urljoin(base, junk))
    nfp = analyse_page({**nf, "status": 200}) if nf.get("body") else {}
    facts["not_found"] = {"probe": junk, "status": nf.get("status"), "title": nfp.get("title"),
                          "h1": nfp.get("h1"), "hrefs": nfp.get("hrefs", [])}
    return facts


# ---------------------------------------------------------------- suggestions
def pct(n: int, d: int) -> str:
    return f"{round(100 * n / d)}%" if d else "-"


def suggest(base: str, pages: list[dict], facts: dict, sitemap: dict, sampled: bool = False) -> dict:
    ok = [p for p in pages if p.get("status") == 200 and "title" in p]
    by_path = {p["path"]: p for p in ok}
    home = by_path.get("/", {})
    s: dict[str, dict] = {}

    def put(cid, status, evidence, details=None):
        s[cid] = {"suggested_status": status, "evidence": evidence, "details": details or []}

    # --- IA
    nav = []
    for a in home.get("header_links", []):
        href, text = a["href"], a["text"].strip()
        if not text or href in ("/", "#", "") or href.startswith("#") or text.lower() in ("search", "skip to content"):
            continue
        if text not in [n["text"] for n in nav]:
            nav.append({"text": text, "href": href})
    put("IA-01", "pass" if 0 < len(nav) <= 6 else ("fail" if nav else "not_checked"),
        f"{len(nav)} top-nav items: " + ", ".join(n["text"] for n in nav), nav)

    legacy = [p["path"] for p in ok if p["scheme"] in ("legacy-modules", "final-week-html", "final-week-legacy")
              or p["path"].endswith(".html")]
    schemes = Counter(p["scheme"] for p in ok)
    put("IA-09", "pass" if not legacy else "fail",
        f"{len(legacy)} pages on legacy URL schemes; pages by scheme: " + ", ".join(f"{k} {v}" for k, v in schemes.most_common()),
        legacy[:15])

    mism = []
    for n in nav:
        target = by_path.get(norm_path(urljoin(base, n["href"])))
        if target and target.get("h1"):
            h1 = target["h1"][0]
            if n["text"].lower() not in h1.lower() and h1.lower() not in n["text"].lower():
                mism.append(f"nav '{n['text']}' opens H1 '{h1}'")
    put("IA-07", "fail" if mism else "partial",
        ("; ".join(mism[:6])) if mism else "Nav labels match their H1s; breadcrumbs and cards still need reading",
        mism)

    groups = defaultdict(list)
    for p in ok:
        if p.get("h1"):
            key = re.sub(r"[^a-z0-9 ]", "", TITLE_CODE.sub("", p["h1"][0]).lower()).strip()
            if key:
                groups[key].append(p["path"])
    dups = {k: v for k, v in groups.items() if len(v) > 1}
    put("IA-13", "fail" if dups else "partial",
        f"{len(dups)} H1s appear on more than one URL (possible duplicate or twin pages)"
        if dups else "No duplicate H1s; cross-hub titles still need reading",
        [f"{k}: {', '.join(v[:4])}" for k, v in list(dups.items())[:15]])

    # --- FV
    hub_flags = []
    for p in ok:
        if p["path"] in HUB_PATHS:
            sw = {k: v for k, v in p.get("status_words", {}).items() if k in ("coming soon", "on hold")}
            if sw:
                hub_flags.append(f"{p['path']}: " + ", ".join(f"{k} x{v}" for k, v in sw.items()))
    put("FV-03", "fail" if hub_flags else "pass",
        "; ".join(hub_flags) if hub_flags else "No Coming soon / On hold on hub pages", hub_flags)

    blocked = [(p["path"], p["status_words"]["blocked"]) for p in ok if p.get("status_words", {}).get("blocked")]
    put("FV-01", "fail" if blocked else "not_checked",
        (f"'Blocked' in served HTML on {len(blocked)} pages (max {max(b for _, b in blocked)}); confirm in the browser"
         if blocked else "Not in served HTML; badges may render client-side, so check in the browser"),
        [f"{a}: {b}" for a, b in sorted(blocked, key=lambda t: -t[1])[:10]])

    stubs = [p["path"] for p in ok if p["scheme"] == "learn" and p["path"] not in HUB_PATHS
             and (p.get("stub") or p.get("words", 999) < 150)]
    put("FV-05", "fail" if stubs else "pass",
        f"{len(stubs)} curriculum pages look like stubs (paused/no lessons or under 150 words)" if stubs else "No stub pages found",
        stubs[:15])

    found = []
    for path in ("/", "/learn", "/design", "/casebook", "/practice", "/guide", "/learning-map", "/interview", "/final-week"):
        p = by_path.get(path)
        if p and p.get("count_claims"):
            found.append(f"{path}: " + ", ".join(p["count_claims"][:8]))
    put("FV-04", "not_checked",
        "Counts claimed on home and hubs are listed below; compare them by reading" if found else "No count claims found",
        found)

    # --- PQ
    content = [p for p in ok if p["path"] not in HUB_PATHS and p["scheme"] not in ("utility", "start")]
    no_shell = []
    nav_hrefs = {n["href"] for n in nav}
    for p in content:
        have = len(nav_hrefs & set(p.get("hrefs", []))) if nav_hrefs else 0
        if nav_hrefs and have < max(1, len(nav_hrefs) // 2):
            no_shell.append(p["path"])
    put("PQ-01", "fail" if no_shell else ("pass" if nav_hrefs else "not_checked"),
        f"{len(no_shell)} of {len(content)} content pages lack the site's top-nav links" if nav_hrefs else "Top nav not found on home",
        no_shell[:15])

    labels = Counter(l for p in ok for l in p.get("objective_labels", []))
    put("PQ-03", "pass" if len(labels) <= 1 else "fail",
        f"{len(labels)} objective labels in use: " + ", ".join(f"'{k}' on {v} pages" for k, v in labels.most_common()),
        list(labels))

    dup_time, mismatch = [], []
    for p in ok:
        r, c = p.get("read_times", []), p.get("clock_times", [])
        if r and c:
            dup_time.append(p["path"])
            if set(r) != set(c):
                mismatch.append(f"{p['path']}: {r} vs {c}")
    put("PQ-04", "fail" if mismatch else ("partial" if dup_time else "pass"),
        f"{len(dup_time)} pages show two reading times; {len(mismatch)} disagree", mismatch[:15] or dup_time[:15])

    leaks = [(p["path"], k, v[0]) for p in ok for k, v in p.get("hits", {}).items() if k.startswith("leak")]
    put("PQ-07", "fail" if leaks else "pass",
        f"{len(leaks)} build-artefact hits on {len({l[0] for l in leaks})} pages",
        [f"{a} [{b}] …{c}…" for a, b, c in leaks[:20]])

    coded = [f"{p['path']}: {p['title']}" for p in ok if p.get("title_code") or p.get("h1_code")]
    put("PQ-08", "fail" if coded else "pass", f"{len(coded)} pages have internal codes in <title> or H1", coded[:15])

    copy = [(p["path"], k, v[0]) for p in ok for k, v in p.get("hits", {}).items() if k.startswith("copy")]
    put("PQ-09", "fail" if copy else "partial",
        f"{len(copy)} copy-bug hits" if copy else "No pattern hits; contradictions (e.g. 'six' listing seven) need reading",
        [f"{a} [{b}] …{c}…" for a, b, c in copy[:20]])

    spell = []
    for i, (name, _, _) in enumerate(SPELLING):
        us = sum(p.get("spelling", {}).get(name, [0, 0])[0] for p in ok)
        uk = sum(p.get("spelling", {}).get(name, [0, 0])[1] for p in ok)
        if us and uk:
            spell.append(f"{name}: US {us}, UK {uk}")
    put("PQ-10", "fail" if spell else "pass", "; ".join(spell) if spell else "One spelling system in use", spell)

    long_pages = sorted(((p["words"], p["path"]) for p in ok if p.get("words", 0) > 2500), reverse=True)
    put("PQ-12", "fail" if long_pages else "pass",
        f"{len(long_pages)} pages over 2,500 words (tabbed pages count all tabs; confirm per tab in the browser)",
        [f"{w} words {pth}" for w, pth in long_pages[:15]])

    lessons = [p for p in content if p["scheme"] in ("learn", "casebook", "practice", "legacy-modules", "interview")]
    dated = sum(1 for p in lessons if p.get("updated_date"))
    authored = sum(1 for p in lessons if p.get("author_line"))
    status = "pass" if lessons and dated == len(lessons) and authored == len(lessons) else (
        "partial" if dated or authored else "fail")
    put("PQ-15", status if lessons else "not_checked",
        f"Last-updated date on {pct(dated, len(lessons))}, author line on {pct(authored, len(lessons))} of {len(lessons)} content pages")

    # --- PR
    host = urlparse(base).netloc
    oh = facts.get("old_host")
    if host.endswith("vercel.app"):
        put("PR-01", "fail", f"Served from {host}")
    elif oh and oh["redirects_to_base"] and oh["permanent"]:
        put("PR-01", "pass", f"Served from {host}; {oh['host']} permanently redirects here")
    elif oh:
        put("PR-01", "partial", f"Served from {host}, but {oh['host']} ends at {oh['final_url']} "
                                f"(HTTP {oh['final_status']}, hops {oh['hops']}); it should 301 to {host}")
    else:
        put("PR-01", "pass", f"Served from {host}")

    og = sum(1 for p in ok if p.get("og_image"))
    card = home.get("twitter_card")
    put("PR-02", "pass" if og == len(ok) and card == "summary_large_image" else ("partial" if og else "fail"),
        f"og:image on {og} of {len(ok)} pages; homepage twitter:card = {card!r}")

    canon = [p for p in ok if p.get("canonical")]
    put("PR-03", "pass" if len(canon) == len(ok) else ("partial" if canon else "fail"),
        f"canonical tag on {len(canon)} of {len(ok)} pages")

    put("PR-04", "pass" if home.get("analytics") else "not_checked",
        "Analytics script found in served HTML" if home.get("analytics") else "None in served HTML; confirm in the browser (may load client-side)")

    fb = sum(1 for p in content if p.get("feedback_link"))
    put("PR-06", "pass" if content and fb == len(content) else ("partial" if fb else "fail"),
        f"Feedback or report-an-issue link on {fb} of {len(content)} content pages")

    nf = facts.get("not_found", {})
    nf_nav = len(nav_hrefs & set(nf.get("hrefs", []))) if nav_hrefs else 0
    put("PR-07", "pass" if nf.get("status") == 404 and nf_nav >= max(1, len(nav_hrefs) // 2) else "fail",
        f"Probe {nf.get('probe')} -> HTTP {nf.get('status')}, H1 {nf.get('h1')}, {nf_nav} nav links")

    rb = facts.get("robots", {})
    put("PR-08", "pass" if rb.get("status") == 200 and rb.get("names_sitemap") and sitemap.get("status") == 200 else "fail",
        f"robots.txt HTTP {rb.get('status')} (names sitemap: {rb.get('names_sitemap')}); sitemap HTTP {sitemap.get('status')}, {sitemap.get('count')} URLs")

    leg = sitemap.get("legacy_entries", [])
    if not sitemap.get("count"):
        put("PR-09", "fail", f"Sitemap empty or unreadable (HTTP {sitemap.get('status')})")
    else:
        put("PR-09", "pass" if not leg and sitemap.get("lastmod") == sitemap.get("count") else "fail",
            f"{len(leg)} legacy or .html URLs in sitemap; lastmod on {sitemap.get('lastmod')} of {sitemap.get('count')} entries",
            leg[:10])

    one_h1 = sum(1 for p in ok if len(p.get("h1", [])) == 1)
    lang = sum(1 for p in ok if p.get("lang"))
    fav = sum(1 for p in ok if p.get("favicon"))
    put("PR-10", "pass" if one_h1 == lang == fav == len(ok) else "partial",
        f"One H1 on {one_h1}, lang on {lang}, favicon on {fav} of {len(ok)} pages")

    ttfb = [p["ttfb_ms"] for p in ok if p.get("ttfb_ms") is not None]
    med = round(statistics.median(ttfb)) if ttfb else None
    # Concurrent crawl timings from wherever this runs are not comparable with the
    # baseline's single browser load, so the scan only reports them; B7 decides.
    put("PR-12", "not_checked",
        f"Crawl median time to first byte {med} ms over {len(ttfb)} pages (concurrent, from this machine; "
        "information only, decide with browser check B7)" if med is not None else "No timings")

    jl = sum(1 for p in ok if p.get("jsonld"))
    put("PR-13", "pass" if jl == len(ok) else ("partial" if jl else "fail"), f"JSON-LD on {jl} of {len(ok)} pages")

    sh = facts.get("security_headers", {})
    good = sum(1 for v in sh.values() if v)
    put("PR-18", "pass" if good == 4 else ("partial" if good else "fail"),
        ", ".join(f"{k}: {'yes' if v else 'no'}" for k, v in sh.items()))

    extra = facts.get("pages", {})
    about = by_path.get("/about") or extra.get("/about") == 200
    put("PR-05", "partial" if about else "fail",
        "/about exists; read it for builder, FDE background and contact" if about
        else f"/about returns HTTP {extra.get('/about')}")
    changelog = by_path.get("/changelog") or extra.get("/changelog") == 200
    put("PR-15", "pass" if changelog else "fail",
        "/changelog exists" if changelog else f"/changelog returns HTTP {extra.get('/changelog')}")

    draw = [p["path"] for p in ok if p.get("drawing_placeholders")]
    put("PR-20", "fail" if draw else "pass",
        f"{len(draw)} pages serve 'Drawing diagram' placeholders (diagrams drawn after JavaScript)", draw[:10])

    # --- CT
    cases = [p for p in ok if CASEBOOK_ITEM.match(p["path"])]
    cal = [p["path"] for p in cases if p.get("level_calibration")]
    fw = [p for p in ok if FINAL_WEEK_ITEM.match(p["path"])]
    if sampled:
        # counts from a sample say nothing about the whole casebook; never let a
        # sample report the core content as missing
        note = " (sampled crawl: run without --limit to decide)"
        put("CT-01", "not_checked", f"Level calibration on {len(cal)} of {len(cases)} sampled casebook pages" + note)
        put("CT-08", "not_checked", f"{len(cases)} casebook pages in the sample" + note)
        put("CT-10", "not_checked", f"{len(fw)} final-week pages in the sample" + note)
    else:
        put("CT-01", "pass" if cases and len(cal) == len(cases) else ("partial" if cal else "fail"),
            f"Level calibration found on {len(cal)} of {len(cases)} casebook pages")
        put("CT-08", "pass" if len(cases) >= 33 else "fail",
            f"{len(cases)} casebook design pages found (URL patterns: /modules/15-fde-case-studies/<group>/<slug> "
            "or /casebook/<slug>; if the casebook moved elsewhere, update CASEBOOK_ITEM before trusting this)")
        put("CT-10", "pass" if fw else "fail", f"{len(fw)} final-week review pages found")
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
    """IA-11: every retired URL should permanently redirect to a live page that is not the homepage."""
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
        status = "partial"  # temporary hops, or some retired URLs still served alongside redirected ones
    elif c["permanent redirect"]:
        status = "pass"
    else:
        status = "na"  # nothing retired yet
    return {
        "suggestion": {
            "suggested_status": status,
            "evidence": f"{len(paths)} legacy URLs: " + ", ".join(f"{k} {v}" for k, v in c.most_common())
                        + (" (all still live: restructure not shipped?)" if status == "na" else ""),
            "details": [f"{r['path']} -> {r['kind']} ({r['final_status']}) {r['final_url']}"
                        for r in (bad + [r for r in results if r["kind"] in ("temporary redirect", "still live")])][:25],
        },
        "results": results,
    }


# ---------------------------------------------------------------- output
def write_summary(out: Path, base: str, pages: list[dict], facts: dict, sitemap: dict, sugg: dict, catalog: dict | None) -> None:
    titles = {c["id"]: c["title"] for c in (catalog or {}).get("checks", [])}
    ok = [p for p in pages if p.get("status") == 200]
    errs = [p for p in pages if p.get("status") != 200]
    L = [f"# Scan summary — {time.strftime('%Y-%m-%d')}", "", f"Base: {base}  ",
         f"Sitemap: HTTP {sitemap.get('status')}, {sitemap.get('count')} URLs; crawled {len(pages)}, {len(ok)} OK, {len(errs)} not OK", ""]
    if len(pages) < (sitemap.get("count") or 0):
        L += ["**Sampled crawl** (--limit): good for a quick look, not for a recorded audit. "
              "Counts and percentages below cover the sample only.", ""]
    if facts.get("home_error"):
        L += [f"**Could not reach the site:** {facts['home_error']}", ""]
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
    ap.add_argument("--base", required=True, help="site root, e.g. https://forwarddeployedprep.com")
    ap.add_argument("--out", required=True, help="audit folder, e.g. .website_spec/site-audits/2026-11-20")
    ap.add_argument("--limit", type=int, help="crawl at most N pages (hubs first, then a sample per URL scheme)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--delay", type=float, default=0.3, help="max random delay per request, seconds")
    ap.add_argument("--legacy", help="file of retired paths to test for permanent redirects (IA-11)")
    ap.add_argument("--old-host", default="forward-deployed-sigma.vercel.app",
                    help="original host; after a domain move PR-01 checks it permanently redirects to --base")
    ap.add_argument("--catalog", default=str(Path(__file__).resolve().parent / "data" / "checks.json"))
    args = ap.parse_args(argv)

    base = args.base.rstrip("/")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(Path(args.catalog).read_text()) if Path(args.catalog).exists() else None

    facts = site_facts(base, args.old_host)
    if facts.get("home_status") != 200:
        why = facts.get("home_error") or f"homepage returned HTTP {facts.get('home_status')}"
        print(f"Cannot audit {base}: {why}.", file=sys.stderr)
        if facts.get("home_status") in (401, 403):
            print("This looks like deployment protection or a firewall: use the public production URL.", file=sys.stderr)
        print("If this shell has no internet access, fall back to WebFetch for the sitemap and key pages (see the site-audit SKILL.md).", file=sys.stderr)
        return 3
    locs, sitemap = read_sitemap(base)
    all_urls = sorted({rebase(u, base) for u in locs} | {base + "/"})
    urls = choose(all_urls, args.limit)
    sampled = len(urls) < len(all_urls)
    print(f"Crawling {len(urls)} of {len(all_urls)} pages from {base} ...", file=sys.stderr)
    pages = crawl(base, urls, args.workers, args.delay)
    ok = sum(1 for p in pages if p.get("status") == 200)
    if ok < max(3, len(pages) // 2):
        out.joinpath("inventory.json").write_text(json.dumps({"base": base, "pages": pages, "site": facts}, indent=1), encoding="utf-8")
        print(f"Only {ok} of {len(pages)} pages returned 200, so the scan would mislead; no suggestions written. "
              f"See {out}/inventory.json for the statuses.", file=sys.stderr)
        return 4
    sugg = suggest(base, pages, facts, sitemap, sampled)

    if args.legacy:
        red = check_legacy(base, Path(args.legacy), args.workers)
        sugg["IA-11"] = red["suggestion"]
        out.joinpath("redirects.json").write_text(json.dumps(red["results"], indent=2), encoding="utf-8")

    inv = {"base": base, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "sitemap": sitemap,
           "site": facts, "pages": pages}
    out.joinpath("inventory.json").write_text(json.dumps(inv, indent=1, ensure_ascii=False), encoding="utf-8")
    out.joinpath("scan-checks.json").write_text(json.dumps(sugg, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary(out, base, pages, facts, sitemap, sugg, catalog)
    fails = sum(1 for v in sugg.values() if v["suggested_status"] == "fail")
    print(f"Done: {len(pages)} pages, {len(sugg)} checks suggested ({fails} fail). See {out}/scan-summary.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
