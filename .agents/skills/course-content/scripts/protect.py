"""Check theory pages against the course-content rules that tests do not cover.

    uv run python .claude/skills/course-content/scripts/protect.py [--rewrite] <page.md> ...

Always: fail on any fenced block other than ```mermaid (pages are theory only; notebooks hold the code).
--rewrite: also fail when a protected block (Mermaid fence, animated or lab marker, image reference) of
`git show HEAD:<page>` was removed, changed or reordered. New Mermaid blocks may be added.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FENCE = re.compile(r"^```.*?^```[ \t]*$", re.M | re.S)
MARKER = re.compile(r"^<!-- (?:animated|lab): .*?-->[ \t]*$|!\[[^\]]*\]\([^)]*\)", re.M)


def protected(text: str) -> list[str]:
    """Mermaid fences and diagram/lab markers, in page order."""
    hits = [(m.start(), m.group()) for m in FENCE.finditer(text) if m.group().startswith("```mermaid")]
    hits += [(m.start(), m.group()) for m in MARKER.finditer(text)]
    return [s for _, s in sorted(hits)]


def code_blocks(text: str) -> list[str]:
    return [m.group().split("\n", 1)[0] for m in FENCE.finditer(text) if not m.group().startswith("```mermaid")]


def kept(old: list[str], new: list[str]) -> bool:
    """Every old block still present, unchanged and in order; only new Mermaid fences may be added."""
    it = iter(new)
    if not all(any(b == n for n in it) for b in old):
        return False
    extra = list(new)
    for b in old:
        extra.remove(b)
    return all(b.startswith("```mermaid") for b in extra)


def head(path: str) -> str | None:
    r = subprocess.run(["git", "show", f"HEAD:./{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def main(argv: list[str]) -> int:
    rewrite = "--rewrite" in argv
    files = [a for a in argv if a != "--rewrite"]
    if not files:
        sys.exit(__doc__)
    bad = 0
    for f in files:
        text = Path(f).read_text()
        for line in code_blocks(text):
            print(f"FAIL {f}: code block {line!r}; pages are theory only")
            bad += 1
        if rewrite:
            old = head(f)
            if old is None:
                print(f"SKIP {f}: not in HEAD, nothing to compare")
            elif not kept(protected(old), protected(text)):
                print(f"FAIL {f}: protected blocks differ from HEAD ({len(protected(old))} before, {len(protected(text))} now)")
                bad += 1
    print(f"{len(files)} page(s), {bad} failure(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
