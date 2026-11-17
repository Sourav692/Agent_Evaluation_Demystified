"""Resolve a module (and optionally a lesson or topic) to everything the course-content skill needs.

    uv run python .claude/skills/course-content/scripts/resolve.py <module> [<lesson or topic>]

<module> is a number (10, M10, m10), a key (lifecycle) or words from the title ("rag lifecycle").
<lesson or topic> is a lesson number (3, 10.3) or words from a lesson title or a key concept.
A single argument like "10.3" means module 10, lesson 3. Prints JSON: paths, lessons with their theory
folder and notebooks, concepts and which page has each, labs and animated diagrams already present.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from curriculum_lib import items, lesson_dir, load, module_dir, theory_dir  # noqa: E402


def words(s):
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def best(query, options):
    """The option whose text shares the most words with the query; ties or no overlap mean no match."""
    q = words(query)
    scored = sorted(((len(q & words(text)) / max(len(q), 1), key) for key, text in options), reverse=True)
    if not scored or scored[0][0] == 0 or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        return None, [k for s, k in scored[:5] if s > 0]
    return scored[0][1], []


def find_module(mods, arg):
    m = re.fullmatch(r"[mM]?(\d+)(?:\.(\d+))?", arg.strip())
    if m:
        hit = next((x for x in mods if x["num"] == int(m.group(1))), None)
        return hit, (int(m.group(2)) if m.group(2) else None), []
    hit = next((x for x in mods if x["key"] == arg.strip().lower()), None)
    if hit:
        return hit, None, []
    key, near = best(arg, [(x["key"], f"{x['title']} {x['key']} {' '.join(x['concepts'])}") for x in mods])
    return next((x for x in mods if x["key"] == key), None), None, near


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cur = load()
    mods = cur["modules"]
    mod, lesson_no, near = find_module(mods, argv[0])
    if not mod:
        sys.exit(json.dumps({"error": f"no single module matches {argv[0]!r}", "closest": near}, indent=2))

    d = theory_dir(mod)
    nbs = {}
    for it in items(cur):
        if it.module["key"] == mod["key"] and it.is_notebook:
            nbs.setdefault(it.lesson_no, []).append({"path": it.dest, "optional": it.optional, "tier": it.tier})

    pages = {f"{d}/README.md": "module"}
    lessons = []
    for n, les in enumerate(mod["lessons"], 1):
        folder = lesson_dir(mod, n)  # mandatory/theory/ or optional/theory/
        has = (ROOT / folder / "README.md").exists()
        if has:
            pages[f"{folder}/README.md"] = f"lesson {n}"
        lessons.append({"n": f"{mod['num']}.{n}", "title": les["title"], "folder": folder, "has_page": has,
                        "notebooks": nbs.get(n, [])})

    concepts = {}
    for c in mod["concepts"]:
        where = [p for p in pages if (ROOT / p).exists() and re.search(rf"^## {re.escape(c)}\s*$", (ROOT / p).read_text(), re.M)]
        concepts[c] = where[0] if where else None

    topic = None
    if len(argv) > 1 or lesson_no:
        if lesson_no is None:
            m = re.fullmatch(r"(?:\d+\.)?(\d+)", argv[1].strip())
            if m:
                lesson_no = int(m.group(1))
        if lesson_no:
            topic = {"lesson": lessons[lesson_no - 1] if 0 < lesson_no <= len(lessons) else None}
        else:
            q = " ".join(argv[1:])
            n, near_l = best(q, [(i + 1, l["title"]) for i, l in enumerate(mod["lessons"])])
            c, near_c = best(q, [(c, c) for c in mod["concepts"]])
            topic = {"query": q, "lesson": lessons[n - 1] if n else None, "concept": c,
                     "closest_lessons": [lessons[i - 1]["n"] for i in near_l]}

    out = {
        "module": {"num": f"M{mod['num']:02d}", "key": mod["key"], "title": mod["title"], "part": mod["part"],
                   "level": mod["level"], "hours": mod["hours"], "why": mod["why"], "objectives": mod["objectives"],
                   "lab_brief": mod.get("lab")},
        "paths": {"course": module_dir(mod), "theory": d, "module_page": f"{d}/README.md",
                  "module_page_exists": (ROOT / d / "README.md").exists(), "index_html": f"{d}/index.html"},
        "lessons": lessons,
        "lab_notebooks": nbs.get(0, []),
        "concepts": concepts,
        "labs": [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / module_dir(mod)).glob("*/theory/**/interactive/*.html"))],
        "animated": [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / module_dir(mod)).glob("*/theory/**/diagrams/*.anim.html"))],
        "neighbours": {"previous": next((f"M{x['num']:02d} {x['title']}" for x in mods if x["num"] == mod["num"] - 1), None),
                       "next": next((f"M{x['num']:02d} {x['title']}" for x in mods if x["num"] == mod["num"] + 1), None)},
        "topic": topic,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
