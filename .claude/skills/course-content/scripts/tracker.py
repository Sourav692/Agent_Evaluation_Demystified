"""Refresh REWRITE_TRACKER.md: page counts from the repo, status columns kept from the file.

    uv run python .claude/skills/course-content/scripts/tracker.py                     # refresh counts only
    uv run python .claude/skills/course-content/scripts/tracker.py --set 23 "Review draft" [--pr "#42"] [--note "..."]

Counts (lessons, lesson pages, pages in the new style) are computed every run. Status, Updated, PRs and
Notes are hand-set through --set and preserved otherwise. A page is in the new style when it carries
the `<!-- format: approved -->` line that a course-content rewrite writes (references/approved-format.md).
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from curriculum_lib import lesson_dir, load  # noqa: E402

TRACKER = ROOT / "REWRITE_TRACKER.md"
STATUSES = ["Not started", "Review draft", "In progress", "In PR", "Live"]
HEAD = "| # | Module | Lessons | Pages | New style | Status | Updated | PRs | Notes |"


def new_style(text: str) -> bool:
    return "<!-- format: approved -->" in text


def counts(module: dict) -> tuple[int, int, int]:
    pages = new = 0
    for n in range(1, len(module["lessons"]) + 1):
        f = ROOT / lesson_dir(module, n) / "README.md"
        if f.exists():
            pages += 1
            new += new_style(f.read_text())
    return len(module["lessons"]), pages, new


def saved() -> dict[int, list[str]]:
    """Status, Updated, PRs, Notes per module number, from the current file."""
    rows = {}
    if TRACKER.exists():
        for line in TRACKER.read_text().splitlines():
            m = re.match(r"\| (\d+) \|", line)
            if m:
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows[int(m.group(1))] = cells[5:9]
    return rows


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", nargs=2, metavar=("MODULE", "STATUS"))
    ap.add_argument("--pr", default=None, help="PR to add, e.g. '#42'")
    ap.add_argument("--note", default=None, help="replaces the Notes cell")
    a = ap.parse_args(argv)

    cur = load()
    parts = {p["id"]: p for p in cur["parts"]}
    rows = saved()
    if a.set:
        num, status = int(a.set[0].lower().lstrip("m")), a.set[1]
        if status not in STATUSES:
            sys.exit(f"status must be one of {STATUSES}")
        st, _, prs, note = rows.get(num, ["", "", "", ""])
        if a.pr and a.pr not in prs.split():
            prs = f"{prs} {a.pr}".strip()
        rows[num] = [status, datetime.date.today().isoformat(), prs, note if a.note is None else a.note]

    out, tally, part = [], dict.fromkeys(STATUSES, 0), None
    for m in cur["modules"]:
        if m["part"] != part:
            part = m["part"]
            p = parts[part]
            out += ["", f"## Part {p['num']} · {p['title']}", "", HEAD, "|---|---|---|---|---|---|---|---|---|"]
        lessons, pages, new = counts(m)
        st, upd, prs, note = rows.get(m["num"], ["Not started", "", "", ""])
        tally[st] = tally.get(st, 0) + 1
        out.append(f"| {m['num']} | {m['title']} | {lessons} | {pages} | {new} / {pages} | {st} | {upd} | {prs} | {note} |")

    summary = " · ".join(f"{k}: {v}" for k, v in tally.items())
    TRACKER.write_text("\n".join([
        "# Theory rewrite tracker",
        "",
        "Progress of rewriting every module's theory pages in the M22 style (theory only, no code, "
        "project pages for notebook-only builds). The `course-content` skill updates this file whenever it "
        "creates, rewrites or reviews a module.",
        "",
        "- **Lessons, Pages, New style**: computed by `.claude/skills/course-content/scripts/tracker.py` from the repo.",
        "- **Status**: `Not started` → `Review draft` (drafts shown, nothing applied) → `In progress` "
        "(pages being edited) → `In PR` → `Live` (merged and on forwarddeployedprep.com).",
        "- **Updated, PRs, Notes**: set with `tracker.py --set <module> <status> [--pr '#N'] [--note '...']`.",
        "",
        f"**Modules:** {summary}",
        *out,
        "",
    ]))
    print(f"{TRACKER.relative_to(ROOT)}: {summary}")


if __name__ == "__main__":
    main(sys.argv[1:])
