"""Export course lesson pages as Forward Deployed lesson pairs: Markdown with frontmatter plus a self-contained HTML page.

    uv run python .claude/skills/course-content/scripts/export_lesson.py <lesson README.md | draft.md=README.md> ... [--out DIR] [--md-only]

`draft.md=README.md` exports a draft (rewrite review) as if it were that lesson page.

The course README stays the one source. For each page this writes
<out>/<track slug>/<module slug>/<NN>-<lesson slug>.md (default out: site-export/, git-ignored), then renders the
.html beside it with standalone/scripts/build_site.py. Frontmatter comes from curriculum.yaml and
docs/fde-site-slugs.yaml; the subtitle from the page's `<!-- subtitle: ... -->` line. Relative links become GitHub
links, diagram and lab markers are dropped (the Mermaid source stays), Key Takeaways becomes Summary, and the
previous/next footer becomes a Next section.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from curriculum_lib import load, lesson_pages  # noqa: E402

GH = "https://github.com/Sourav692/rag-agents-engineering/blob/main/"
RAW = "https://raw.githubusercontent.com/Sourav692/rag-agents-engineering/main/"
COLAB = "https://colab.research.google.com/github/Sourav692/rag-agents-engineering/blob/main/"
BUILD = Path(__file__).resolve().parents[1] / "standalone" / "scripts" / "build_site.py"
LEVEL = {"foundation": "beginner", "core": "intermediate", "advanced": "advanced", "expert": "advanced"}


def find(page: str, cur: dict):
    for m in cur["modules"]:
        for n, p in lesson_pages(m).items():
            if p == page:
                return m, n
    sys.exit(f"{page}: not a lesson page in curriculum.yaml")


def to_github(md: str, page: str) -> str:
    def fix(mo):
        bang, label, target = mo.group(1), mo.group(2), mo.group(3)
        if target.startswith(("http", "#", "mailto:")):
            return mo.group(0)
        path, _, frag = target.partition("#")
        full = os.path.normpath(os.path.join(os.path.dirname(page), path))
        return f"{bang}[{label}]({(RAW if bang else GH) + full}{'#' + frag if frag else ''})"
    return re.sub(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)", fix, md)


def export(page: str, cur: dict, slugs: dict, out: Path, text: str | None = None) -> Path:
    m, n = find(page, cur)
    part = next(p for p in cur["parts"] if p["id"] == m["part"])
    track = slugs["tracks"][m["part"]]
    mod_slugs = slugs["modules"][m["key"]]
    titles = [les["title"] for les in m["lessons"]]
    in_part = [x["key"] for x in cur["modules"] if x["part"] == m["part"]]

    src = text if text is not None else (ROOT / page).read_text()
    sub = re.search(r"<!-- subtitle: (.*?) -->", src)
    body = src.split("\n", 1)[1]                                          # drop the H1
    head = re.search(r"^\*\[M\d+ theory\].*$", body, re.M)
    nbs = re.findall(r"\[`([^`]+)`\]\(([^)\s]+)\)( \(optional\))?", head.group(0)) if head else []
    body = re.sub(r"^\*\[M\d+ theory\].*\n", "", body, count=1, flags=re.M)  # header line
    body = re.sub(r"^<!-- (?:subtitle|format|animated|lab): .*?-->[ \t]*\n", "", body, flags=re.M)
    body = re.split(r"\n---\n\*Previous:", body)[0].rstrip() + "\n"
    if nbs:  # the same "Run the notebooks" section the site's importer adds
        rows = []
        for file, target, opt in nbs:
            full = os.path.normpath(os.path.join(os.path.dirname(page), target))
            colab = f"[Open in Colab]({COLAB + full})" if file.endswith(".ipynb") else "Run locally"
            title = re.sub(r"^\d+[a-z]?_", "", file.rsplit(".", 1)[0]).replace("_", " ")
            rows.append(f"| {title[:1].upper() + title[1:]}{opt} | [Open on GitHub]({GH + full}) | {colab} |")
        section = ("## Run the notebooks\n\nThe code for this lesson is in these notebooks. Colab runs one in your browser: "
                   "install the packages its first cell imports and set the API keys it reads. To run every notebook as written, "
                   "clone the repository and use its uv environment.\n\n| Notebook | GitHub | Colab |\n|---|---|---|\n" + "\n".join(rows) + "\n\n")
        body = body.replace("\n## Key Takeaways\n", "\n" + section + "## Key Takeaways\n", 1)
    body = body.replace("\n## Key Takeaways\n", "\n## Summary\n")
    nxt = next((titles[k - 1] for k in sorted(lesson_pages(m)) if k > n), None)
    if nxt:
        body += f"\n## Next\n\n**{nxt}**\n"
    body = to_github(body, page)

    fm = {
        "title": titles[n - 1],
        **({"subtitle": sub.group(1)} if sub else {}),
        "track": "AI Engineering",
        "module_group": part["title"],
        "module_code": f"{track['code']}.{in_part.index(m['key']) + 1}",
        "module_name": m["title"],
        "lesson": n,
        "lessons": titles,
        "level": LEVEL.get(m.get("level"), "intermediate"),
        "reading_time": f"{max(1, round(len(body.split()) / 200))} min",
        "source": "From the RAG & Agents Engineering course",
        "author": "Sourav Banerjee",
    }
    slug = mod_slugs["lessons"].get(titles[n - 1], re.sub(r"[^a-z0-9]+", "-", titles[n - 1].lower()).strip("-"))
    dst = out / track["slug"] / mod_slugs["slug"] / f"{n:02d}-{slug}.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    head = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000)
    dst.write_text(f"---\n{head}---\n\n# {fm['title']}\n\n" + (f"*{fm['subtitle']}*\n\n" if sub else "") + body.lstrip())
    return dst


def main(argv: list[str]) -> int:
    out = ROOT / "site-export"
    if "--out" in argv:
        i = argv.index("--out")
        out = Path(argv[i + 1]).resolve()
        del argv[i:i + 2]
    md_only = "--md-only" in argv
    args = [a for a in argv if a != "--md-only"]
    if not args:
        sys.exit(__doc__)
    cur, slugs = load(), yaml.safe_load((ROOT / "docs/fde-site-slugs.yaml").read_text())
    for arg in args:
        draft, _, page = arg.rpartition("=")
        page = os.path.relpath(Path(page).resolve(), ROOT)
        dst = export(page, cur, slugs, out, Path(draft).read_text() if draft else None)
        print(f"wrote {dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst}")
        if not md_only:
            subprocess.run([sys.executable, str(BUILD), str(dst)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
