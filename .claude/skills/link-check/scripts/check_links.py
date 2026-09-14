#!/usr/bin/env python3
"""Report relative markdown links whose targets do not exist.

Usage: check_links.py [path ...]    (defaults to the repo root)
Exit code 1 if any link is broken, else 0.
"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

# [text](target) — images count too. The target may contain balanced parens one level
# deep (`Analysis (v2).md`) or escaped ones, so plain [^)]+ would truncate it.
LINK_RE = re.compile(
    r"\[[^\]]*\]\(\s*((?:[^()\s\\]|\\.|\([^()\s]*\))+)\s*(?:\"[^\"]*\")?\s*\)"
)
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:", "data:")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def tracked_markdown(root: Path, scopes: list[Path]) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    files = [root / p for p in out.stdout.split("\0") if p]
    # Untracked .md files are worth checking too (e.g. a brand-new index).
    extra = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard", "--", "*.md"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    files += [root / p for p in extra.stdout.split("\0") if p]
    if scopes:
        files = [f for f in files if any(_within(f, s) for s in scopes)]
    return sorted(set(files))


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def check(md: Path, root: Path) -> list[tuple[int, str]]:
    broken = []
    try:
        lines = md.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return broken
    in_fence = False
    for lineno, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for raw in LINK_RE.findall(line):
            target = raw.split("#", 1)[0]
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            target = unquote(target.replace("\\", ""))
            base = root if target.startswith("/") else md.parent
            resolved = (base / target.lstrip("/")).resolve()
            if not resolved.exists():
                broken.append((lineno, raw))
    return broken


def main() -> int:
    root = repo_root()
    scopes = [Path(a).resolve() for a in sys.argv[1:]]
    for s in scopes:
        if not s.exists():
            print(f"error: no such path: {s}", file=sys.stderr)
            return 2

    total = 0
    for md in tracked_markdown(root, scopes):
        broken = check(md, root)
        if not broken:
            continue
        print(f"\n{md.relative_to(root)}")
        for lineno, target in broken:
            print(f"  line {lineno}: {target}")
            total += 1

    scanned = len(tracked_markdown(root, scopes))
    if total:
        print(f"\n{total} broken link(s) across {scanned} markdown file(s).")
        return 1
    print(f"All relative links resolve ({scanned} markdown file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
