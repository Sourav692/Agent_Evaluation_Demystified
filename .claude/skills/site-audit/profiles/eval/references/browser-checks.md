# Browser checks

Some checks can only be decided in a real browser: Mermaid diagrams (drawn after load), the labs and the drill (built by JavaScript), layout widths and the look of copied pages. Use Claude in Chrome (`mcp__claude-in-chrome__*`) when it is available. If no browser tool is available, record these checks as `not_checked` with the reason — never infer them from served HTML.

## Ground rules

- Work in a new tab you open yourself; close it when done.
- **Do not clear localStorage or site data.** The drill keeps the owner's recall ratings under the key `evalround.v1`; clearing it destroys them. Read it, never write it.
- Do not click any reset or clear control (it may open a confirm dialog that blocks the browser session); read its markup instead.
- Batch actions with `browser_batch` where possible. Save screenshots you want in the report with `save_to_disk: true`.
- Page list: take URLs from this audit's `inventory.json` (`pages[].path`, `kind`, `mermaid`).

## B1 Index meta, nav and first screen (PR-02, PR-03, PR-04, PR-10, IA-01, ON-01, IA-10)

Open `/index.html`, wait 2 s, run:

```js
(() => {
  const q = s => document.querySelector(s);
  const meta = n => (q(`meta[property="${n}"]`) || q(`meta[name="${n}"]`))?.content || null;
  const nav = [...document.querySelectorAll('header nav a')].filter(a => a.offsetParent !== null).map(a => a.textContent.trim());
  return {
    title: document.title, description: meta('description'), ogImage: meta('og:image'), ogTitle: meta('og:title'),
    twitterCard: meta('twitter:card'), canonical: q('link[rel=canonical]')?.href || null,
    icons: [...document.querySelectorAll('link[rel*=icon]')].map(l => l.href),
    lang: document.documentElement.lang, h1s: document.querySelectorAll('h1').length,
    jsonLd: document.querySelectorAll('script[type="application/ld+json"]').length,
    analytics: [...document.scripts].map(s => s.src).filter(s => /analytics|gtag|plausible|insights|posthog|umami|fathom/.test(s)),
    search: !!q('input[type=search], [role=search], [aria-label*=earch i]'),
    navItems: nav
  };
})()
```

ON-01: screenshot the first screen. Pass when it names the audience, states the promise and offers one primary call to action (at most one secondary). Section cards alone are not a call to action.

IA-10: also press Cmd-K (or Ctrl-K) and look for a search dialog. Pass only if a search finds a page by keyword.

## B2 Diagrams render (FV-01)

Open every page with `mermaid > 0` in `inventory.json` (the theory pages and most explainers). Diagrams render lazily, as each one nears the viewport (since 2026-10-15), so a count straight after load undercounts. Scroll to each diagram and give it up to 10 s:

```js
const boxes = [...document.querySelectorAll('.mermaid')];
for (const b of boxes) {
  b.scrollIntoView();
  const t = Date.now();
  while (!b.querySelector('svg') && Date.now() - t < 10000) await new Promise(r => setTimeout(r, 100));
}
const raw = boxes.filter(b => !b.querySelector('svg') && /\b(flowchart|graph|sequenceDiagram|stateDiagram)\b/.test(b.textContent));
({ diagrams: boxes.length, rendered: boxes.filter(b => b.querySelector('svg')).length,
   rawLeft: raw.length, example: raw[0]?.textContent.slice(0, 80) || null })
```

Pass when `rawLeft` is 0 on every page. A failure here usually means the Mermaid CDN script (pinned `mermaid@11.17.2`) failed to load, or the lazy loader in `MERMAID_SCRIPT` (`site/build.py`) broke.

## B3 Interactive labs respond (FV-02)

For each lab (`/00-evaluation-index.html`, `/01-…` to `/05-…`): note the visible metric numbers, operate the lab's control once (Lab 01 has a range slider for K; the others use buttons — click the first non-reset button), then read the numbers again.

```js
(() => [...document.querySelectorAll('main, body')].pop().innerText.match(/\b[01]\.\d{2}\b/g)?.slice(0, 12))()
```

Pass when the numbers change after the action on every lab. Then read console errors with `read_console_messages` (pattern `error|Error|Uncaught`); any error fails the lab.

## B4 The drill (FV-03, PR-16)

Open `/evaluation-round-drill.html`, wait 2 s:

```js
(() => {
  let saved = null; try { saved = localStorage.getItem('evalround.v1'); } catch (e) {}
  const hidden = [...document.querySelectorAll('details:not([open]), [hidden], .answer')].length;
  const resets = [...document.querySelectorAll('button')].filter(b => /reset|clear/i.test(b.textContent))
    .map(b => ({ text: b.textContent.trim(), onclick: b.getAttribute('onclick') }));
  return { savedRatingsBytes: saved ? saved.length : 0, hiddenAnswers: hidden, resetButtons: resets };
})()
```

- FV-03: reveal one answer, rate it, switch the weak-only filter on and off. Pass when all three work. `savedRatingsBytes` > 0 means the owner has history: judge first-visit behaviour from what the code does with an empty store, not by clearing it.
- PR-16: reload; the rating you just gave should persist. For safe reset, read the reset button's handler in the page source (search for `confirm(`). Do not click it.

## B5 Fit at desktop and phone width (PQ-09, PR-11)

Try `resize_window` to 390×844, reload, and on the index, an explainer with a table (e.g. `/06-the-release-gate-and-ci.html`), `/question-bank.html`, `/01-deterministic-retrieval-metrics.html` and the drill run:

```js
JSON.stringify({ vw: innerWidth, scrollW: document.documentElement.scrollWidth,
  pageOverflow: document.documentElement.scrollWidth > innerWidth + 1,
  wideBlocks: [...document.querySelectorAll('table, .mermaid svg, pre')].filter(e => {
    const r = e.getBoundingClientRect(); return r.right > innerWidth + 1 && getComputedStyle(e.parentElement).overflowX === 'visible';
  }).length })
```

Pass when `pageOverflow` is false and `wideBlocks` is 0. If `vw` does not change after the resize (window maximised), record PR-11 as `partial` (not verified) and suggest checking with DevTools device mode. Repeat the `wideBlocks` part at desktop width for PQ-09.

## B6 Copied pages look like the site (PQ-02)

Screenshot the top of `/question-bank.html` (rendered), then `/evaluation-round-drill.html`, `/evaluation-study-plan.html`, `/01-deterministic-retrieval-metrics.html` and `/openai-eval-guide-tutorial.html` (copied). Pass when fonts, colours and the header read as one site. Repeat once in dark mode if the OS can be switched; the copied pages' bar has its own dark rules, the pages beneath may not.

## B7 404 page (PR-07)

Navigate to `/this-page-does-not-exist-<random>.html` and screenshot. Pass when the page keeps the site header and links back into the sections. Vercel's plain `404: NOT_FOUND` is a fail.

## B8 Timing (PR-12)

After a normal load of the index:

```js
(() => { const n = performance.getEntriesByType('navigation')[0];
  return { ttfbMs: Math.round(n.responseStart), domContentLoadedMs: Math.round(n.domContentLoadedEventEnd), loadMs: Math.round(n.loadEventEnd) }; })()
```

Reload twice and take the median.

## B9 Lighthouse (PR-17)

From the shell, if Node and a local Chrome are available:

```bash
for p in /index.html /06-the-release-gate-and-ci.html /question-bank.html /01-deterministic-retrieval-metrics.html /evaluation-round-drill.html; do
  npx --yes lighthouse "https://eval-demystified.vercel.app$p" --quiet --chrome-flags="--headless" \
    --only-categories=performance,accessibility,best-practices,seo \
    --output=json --output-path=".website_spec/site-audits/<DATE>/lighthouse$(echo $p | tr / _).json"
done
```

Read each file's `categories.*.score` (0–1, multiply by 100). Pass when all four are 90+ on all five pages; partial when most are. If Lighthouse can't run, record `not_checked` and say why.

## Screenshots for the report

Save four with `save_to_disk: true`: the index, an explainer, a lab and the drill. Name them by audit date. Close the tab when done.
