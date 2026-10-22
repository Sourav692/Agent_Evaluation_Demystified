# Browser checks

Some checks can only be decided in a real browser: things drawn by JavaScript, things the user sees on first visit, layout widths. Use Claude in Chrome (`mcp__claude-in-chrome__*`) when it is available. If no browser tool is available, record these checks as `not_checked` with the reason — never infer them from served HTML.

Why this matters: in the first audit, two findings from page-text reading were wrong (the 404 page was custom, not the framework default; diagrams did render after load). Both were caught only in the browser.

## Ground rules

- Work in a new tab you open yourself; close it when done.
- **Do not clear localStorage or site data.** The site stores the owner's saved answers and progress there, and clearing it destroys them. To judge first-visit badges, read how much progress is stored (read-only snippet below) and interpret the badge count against it.
- Batch actions with `browser_batch` where possible.
- Save screenshots you want in the report with `save_to_disk: true`.

## B1 Homepage meta and launch basics (PR-02, PR-03, PR-04, PR-10, IA-01)

Open the homepage, wait 2 s, run:

```js
(() => {
  const q = s => document.querySelector(s);
  const meta = n => (q(`meta[property="${n}"]`) || q(`meta[name="${n}"]`))?.content || null;
  const nav = [...new Set([...document.querySelectorAll('header a')]
    .filter(a => a.offsetParent !== null && a.getAttribute('href') !== '/')
    .map(a => a.textContent.trim()).filter(Boolean))];
  return {
    title: document.title, ogImage: meta('og:image'), twitterCard: meta('twitter:card'),
    canonical: q('link[rel=canonical]')?.href || null,
    icons: [...document.querySelectorAll('link[rel*=icon]')].map(l => l.href),
    lang: document.documentElement.lang, h1s: document.querySelectorAll('h1').length,
    jsonLd: document.querySelectorAll('script[type="application/ld+json"]').length,
    analytics: [...document.scripts].map(s => s.src).filter(s => /analytics|gtag|plausible|insights|posthog|umami|fathom/.test(s)),
    visibleNavItems: nav
  };
})()
```

Baseline 2026-10-09: no og:image, twitter:card `summary`, no canonical, favicon present, `lang="en"`, 1 H1, no JSON-LD, no analytics, 8 nav items.

ON-08 (one dominant first step): take a screenshot of the homepage hero. Pass when there is one primary call to action and at most one secondary. Baseline: "Choose your path" (primary) and "Explore curriculum" (secondary) — pass.

## B2 First-visit badges (FV-01)

On `/start/paths/fde`, `/design` (or the new casebook hub), `/interview` (or its replacement) and one lesson page, run:

```js
(() => {
  const t = document.body.innerText;
  const blocked = [...document.querySelectorAll('span,div,button')].filter(e => e.textContent.trim() === 'Blocked');
  const tip = blocked[0] && document.getElementById(blocked[0].getAttribute('aria-describedby'))?.textContent;
  let progressKeys = 0; try { progressKeys = Object.keys(localStorage).length; } catch (e) {}
  return { blockedBadges: blocked.length, comingSoon: (t.match(/Coming soon/gi) || []).length,
           onHold: (t.match(/On hold/gi) || []).length, tooltip: tip || null, localStorageKeys: progressKeys };
})()
```

`localStorageKeys` is read-only context: if the owner has saved progress, some badges may reflect it. Baseline: 39 Blocked badges on `/start/paths/fde`, 5 on `/design`, 2 on `/interview`; tooltip "A prerequisite checkpoint is missing or failed. You can still open it (soft gating)."

## B3 Diagrams render and fit (PQ-13, PQ-14)

Open a diagram-heavy lesson (baseline: `/learn/llm-and-retrieval/rag-from-first-principles/the-rag-pipeline-end-to-end`) and a long case (baseline: `/modules/15-fde-case-studies/judgement-and-decomposition/decomposition-classics-67-68-69`). Wait 4 s, then:

```js
(() => {
  const t = document.body.innerText;
  const wide = [...document.querySelectorAll('main svg, article svg')].map(svg => {
    const r = svg.getBoundingClientRect(); const box = svg.parentElement.getBoundingClientRect();
    return { w: Math.round(r.width), container: Math.round(box.width) };
  }).filter(x => x.w > x.container + 4);
  return { drawingPlaceholdersLeft: (t.match(/Drawing diagram/g) || []).length,
           svgCount: document.querySelectorAll('main svg, article svg').length, overflowingDiagrams: wide.length, examples: wide.slice(0, 3) };
})()
```

Baseline: 0 placeholders left and 21 SVGs (PQ-14 pass); RAG pipeline diagram 1,320 px in a 685 px column (PQ-13 fail). Also screenshot (`zoom`) the first diagram to see whether it is clipped.

## B4 Long pages (PQ-12)

On the longest case pages from the scan (`PQ-12` details), for the first tab only:

```js
JSON.stringify({ words: document.body.innerText.split(/\s+/).length,
  h2: document.querySelectorAll('h2').length,
  tabs: [...document.querySelectorAll('[role=tab]')].map(t => t.textContent.trim()),
  pageHeightPx: document.documentElement.scrollHeight })
```

Baseline G01: ~3,900 words, 84 H2s, ~22,500 px, 4 tabs.

## B5 404 page (PR-07)

Navigate to `/this-page-does-not-exist-<random>` and screenshot. Pass when the page keeps the site header and offers links back into the sections. Baseline: custom "Page Not Found" with Learn, Design, Practice, Interview links (pass).

## B6 Mobile (PR-11)

Try `resize_window` to 390×844, reload and screenshot home, a lesson, a case and a hub, then run:

```js
JSON.stringify({ vw: innerWidth, scrollW: document.documentElement.scrollWidth,
  overflow: document.documentElement.scrollWidth > innerWidth + 1,
  menuButton: !![...document.querySelectorAll('button')].find(b => /menu/i.test(b.getAttribute('aria-label') || '')) })
```

If `vw` does not change after the resize (the window may be maximised), the width check cannot be done this way. Do not use an iframe either: the site refuses to be framed. Record PR-11 as `partial` (menu present, width not verified) and suggest the owner checks on a phone or with DevTools device mode. Baseline: hamburger and bottom nav present, width not verified.

## B7 Timing (PR-12)

After a normal load:

```js
(() => { const n = performance.getEntriesByType('navigation')[0];
  return { ttfbMs: Math.round(n.responseStart), domContentLoadedMs: Math.round(n.domContentLoadedEventEnd), loadMs: Math.round(n.loadEventEnd) }; })()
```

Reload twice and take the median. Baseline: ~1.5 s time to first byte on one load.

## B8 Homepage preview, filters, progress tools (FV-06, IA-14, PR-16, CT-05)

- FV-06: type a short answer in the homepage preview and click compare; pass if the strong answer appears. Do not submit any other form.
- IA-14: on the casebook and practice hubs, look for filter controls with counts.
- PR-16: look for export/import of progress; check whether "Clear all my saved answers" asks for confirmation — **do not click it**, read its markup instead (a confirm dialog would also block the browser session).
- CT-05: on one worksheet, look for an AI-feedback or peer-review option.

## B9 Lighthouse (PR-17)

From the shell, if Node and a local Chrome are available (Claude Code on the owner's machine usually has both):

```bash
for p in / /learn <a hub> <a lesson> <a case> <a worksheet>; do
  npx --yes lighthouse "<URL>$p" --quiet --chrome-flags="--headless" \
    --only-categories=performance,accessibility,best-practices,seo \
    --output=json --output-path=".website_spec/site-audits/<DATE>/lighthouse$(echo $p | tr / _).json"
done
```

Read each file's `categories.*.score` (0–1, multiply by 100). Pass when all four are 90+ on all five page types; partial when most are. If Lighthouse can't run (no Node, no Chrome, sandboxed shell), record `not_checked` and say why. Baseline: not run.

## Screenshots for the report

Save four with `save_to_disk: true`: homepage, a hub, a lesson, a case. Name them by audit date. Close the tab when done.
