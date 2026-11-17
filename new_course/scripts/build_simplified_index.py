#!/usr/bin/env python3
"""Build the local browser index from the simplified course's Markdown index."""
from html import escape
from pathlib import Path
import re

COURSE = Path(__file__).resolve().parents[1]
SOURCE = COURSE / "simplified-course-index.md"
OUTPUT = COURSE / "simplified-course-index.html"


def build():
    rows = []
    for line in SOURCE.read_text().splitlines():
        if not re.match(r"\| \d{2} \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        week, title = cells[:2]
        markdown = re.search(r"\]\(([^)]+)\)", cells[2]).group(1)
        lesson = re.search(r"\]\(([^)]+)\)", cells[3]).group(1)
        for destination in (markdown, lesson):
            if not (COURSE / destination).is_file():
                raise FileNotFoundError(destination)
        rows.append((week, title, markdown, lesson))
    if len(rows) != 16:
        raise ValueError(f"Expected 16 weeks, found {len(rows)}")
    reference = (COURSE / rows[0][3]).read_text()
    fonts = "\n".join(re.findall(r"@font-face\{[^}]+\}", reference))
    lessons = "\n".join(
        f'<li id="week-{week}"><span class="week">Week {int(week)}</span>'
        f'<h3><a href="{escape(lesson, quote=True)}">{escape(title)}</a></h3>'
        f'<a class="download" href="{escape(markdown, quote=True)}" download '
        f'aria-label="Download Week {int(week)} Markdown">Download Markdown</a></li>'
        for week, title, markdown, lesson in rows
    )
    first = escape(rows[0][3], quote=True)
    css = '''/* Hallmark · checked: 2026-11-18 · genre: editorial · hero: compact course index · built: the project · v2.0.0 */
/* Critique: keep the approved course typography and make lesson navigation readable offline. */
/* Hallmark · waive 44c · first lesson visible in the initial desktop viewport · course navigation needs a compact introduction rather than a full-screen hero */
/* Hallmark · waive 59 · 64px separates the course introduction from its lesson navigation · related lesson links stay together in this compact course index */
/* Hallmark · waive 78 · the navigation heading is 32px and lesson titles are 24px · retain the course hierarchy for Choose a week rather than another display headline */
:root{--paper:#f7f5f0;--ink:#0c0d12;--text:#2a2b31;--muted:#62615e;--line:#cdcac3;--green:#007439;--button-text:#faf8f5;--focus:#007439;--display:"Bricolage Grotesque",Georgia,serif;--body:Inter,system-ui,sans-serif}
*{box-sizing:border-box}
html{overflow-x:clip;scroll-padding-top:24px}
body{overflow-x:clip;margin:0;background:var(--paper);color:var(--text);font-family:var(--body);font-size:16px;line-height:1.6}
a{color:inherit;text-underline-offset:4px;text-decoration-thickness:1px}
a:hover{color:var(--green)}
a:active{opacity:.8}
a:focus-visible{outline:3px solid var(--focus);outline-offset:5px}
.wrap{width:min(100% - 48px,1120px);margin-inline:auto}
header{padding:24px 0;border-bottom:1px solid var(--line)}
header .wrap{display:flex;justify-content:space-between;gap:24px;align-items:center}
.brand{font-weight:600;text-decoration:none}
header a:last-child{font-size:15px}
main{padding-block:64px}
h1,h2,h3{font-family:var(--display);font-weight:600;color:var(--ink);overflow-wrap:break-word;min-width:0;text-wrap:balance}
h1{font-size:clamp(40px,6vw,72px);line-height:1.06;max-width:800px;margin:0 0 24px}
h2{font-size:32px;line-height:1.2;margin:0}
h3{font-size:24px;line-height:1.3;margin:0}
.intro{font-size:20px;max-width:640px;margin:0 0 32px}
.start{display:inline-block;padding:12px 24px;background:var(--green);color:var(--button-text);font-weight:600;text-decoration:none;border:1px solid var(--green);border-radius:4px}
.start:hover{color:var(--button-text);filter:brightness(.9)}
.hero{padding-bottom:64px}
.section-head{display:flex;justify-content:space-between;gap:24px;align-items:baseline;border-bottom:2px solid var(--ink);padding-bottom:20px}
.section-head p{margin:0;color:var(--muted)}
ol{list-style:none;padding:0;margin:0}
li{display:grid;grid-template-columns:96px minmax(0,1fr) 168px;gap:24px;align-items:baseline;padding:28px 0;border-bottom:1px solid var(--line)}
.week,.download{font-size:15px;color:var(--muted)}
h3 a{text-decoration:none}
h3 a:hover{text-decoration:underline}
.download{justify-self:end}
footer{padding:32px 0 48px;border-top:1px solid var(--line)}
footer p{max-width:680px;margin:0;color:var(--muted)}
.skip{position:absolute;left:12px;top:8px;width:1px;height:1px;clip-path:inset(50%);overflow:clip;white-space:nowrap;background:var(--paper)}
.skip:focus{width:auto;height:auto;clip-path:none;padding:12px;z-index:2}
@media(max-width:640px){.wrap{width:calc(100% - 36px)}header .wrap{align-items:flex-start}main{padding-block:40px}.hero{padding-bottom:48px}.section-head{display:block}.section-head p{margin-top:12px}li{grid-template-columns:64px minmax(0,1fr);gap:12px;padding-block:24px}.download{grid-column:2;justify-self:start}h3{font-size:22px}}
@media print{header,.start,.download,.skip{display:none}main{padding-top:0}.hero{padding-bottom:24px}li{break-inside:avoid;grid-template-columns:64px minmax(0,1fr)}}'''
    document = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Read all sixteen simplified lessons on RAG and agent evaluation, with local HTML pages and Markdown downloads.">
<title>Simplified evaluation course: Weeks 1 to 16</title>
<style>{css}\n{fonts}</style>
</head>
<body id="top">
<a class="skip" href="#main">Skip to lessons</a>
<header><div class="wrap"><a class="brand" href="#top">Agent evaluation</a><a href="#lessons">All lessons</a></div></header>
<main id="main" class="wrap">
<section class="hero" aria-labelledby="course-title">
<h1 id="course-title">Simplified evaluation course</h1>
<p class="intro">Read sixteen lessons on testing and improving RAG and agent systems.</p>
<a class="start" href="{first}">Start Week 1</a>
</section>
<section id="lessons" aria-labelledby="lesson-heading">
<div class="section-head"><h2 id="lesson-heading">Choose a week</h2><p>Follow the lessons in order.</p></div>
<ol>{lessons}</ol>
</section>
</main>
<footer><div class="wrap"><p>Open a lesson title to read its HTML page. Markdown downloads are available for every week. Keep this file beside the weeks folder so all links work locally.</p></div></footer>
</body>
</html>
'''
    OUTPUT.write_text(document)
    print(f"Wrote {OUTPUT}: 16 verified HTML lesson links and 16 Markdown downloads")


if __name__ == "__main__":
    build()
