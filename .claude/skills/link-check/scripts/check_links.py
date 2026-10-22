#!/usr/bin/env python3
"""Report relative markdown links whose targets do not exist.

Usage: check_links.py [--html] [path ...]    (defaults to the repo root)
  --html   also check href="..." links, and scan .html files as well as .md

A link is broken when its target is missing, or when it exists only with different
letter case (macOS ignores case, GitHub does not), judged against the paths git knows
(tracked plus untracked, non-ignored). Exit code 1 if any link is broken, else 0.
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
HREF_RE = re.compile(r'href="([^"]+)"')
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "tel:", "data:", "javascript:")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(out.stdout.strip())


def git_paths(root: Path, *patterns: str) -> list[str]:
    """Tracked plus untracked, non-ignored paths (repo-relative, exact case)."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *patterns],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return [p for p in out.stdout.split("\0") if p]


def known_paths(root: Path) -> set[str]:
    """Every file git knows plus all of their parent folders, in exact case."""
    known = set()
    for f in git_paths(root):
        while f:
            known.add(f)
            f = f.rpartition("/")[0]
    return known


def tracked_markdown(root: Path, scopes: list[Path], html: bool = False) -> list[Path]:
    patterns = ["*.md", "*.html"] if html else ["*.md"]
    files = [root / p for p in git_paths(root, *patterns)]
    if scopes:
        files = [f for f in files if any(_within(f, s) for s in scopes)]
    return sorted(set(files))


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def check(md: Path, root: Path, known: set[str], html: bool = False) -> list[tuple[int, str]]:
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
        targets = LINK_RE.findall(line) + (HREF_RE.findall(line) if html else [])
        for raw in targets:
            target = raw.split("#", 1)[0]
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            target = unquote(target.replace("\\", ""))
            base = root if target.startswith("/") else md.parent
            resolved = (base / target.lstrip("/")).resolve()
            if not resolved.exists():
                broken.append((lineno, raw))
                continue
            try:
                rel = resolved.relative_to(root.resolve()).as_posix()
            except ValueError:
                continue  # outside the repo: existence is all we can check
            if rel and rel != "." and rel not in known:
                broken.append((lineno, f"{raw}  (case mismatch, or not tracked by git)"))
    return broken


def main() -> int:
    root = repo_root()
    args = sys.argv[1:]
    html = "--html" in args
    scopes = [Path(a).resolve() for a in args if a != "--html"]
    for s in scopes:
        if not s.exists():
            print(f"error: no such path: {s}", file=sys.stderr)
            return 2

    known = known_paths(root)
    files = tracked_markdown(root, scopes, html)
    total = 0
    for md in files:
        broken = check(md, root, known, html)
        if not broken:
            continue
        print(f"\n{md.relative_to(root)}")
        for lineno, target in broken:
            print(f"  line {lineno}: {target}")
            total += 1

    scanned = len(files)
    if total:
        print(f"\n{total} broken link(s) across {scanned} markdown file(s).")
        return 1
    print(f"All relative links resolve ({scanned} markdown file(s) scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
