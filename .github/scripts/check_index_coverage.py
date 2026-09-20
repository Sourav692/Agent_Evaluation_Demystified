#!/usr/bin/env python3
"""Fail when INDEX.md stops covering what docs/ contains.

INDEX.md is the repo's lookup table -- "every document, what each section
covers". Nothing enforced that, so a document could be added, or an index
section deleted, without anything noticing. On 2026-09-20 an edit removed three
INDEX.md sections while intending to remove one, and the question bank lost its
entry in a pushed commit.

Two checks, because one does not catch the other:

  MENTIONED   every file under docs/ appears somewhere in INDEX.md.
              Catches a document nobody indexed.

  SECTIONED   every non-README .md under docs/ has its own `### `path`` heading.
              Catches a section that was deleted while still passing MENTIONED,
              because the file is named in the topic tables too -- which is
              exactly how the question bank's removal went unnoticed.

READMEs are folder indexes, listed in INDEX.md's "Folder indexes" table rather
than given a section of their own, so SECTIONED skips them. They must still be
MENTIONED, by folder -- the bare string "README.md" appears throughout INDEX.md
and would otherwise pass every one of them trivially.

Stdlib only; no network, no cost.

    python3 .github/scripts/check_index_coverage.py
"""
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "INDEX.md")


def docs_files():
    """Tracked files plus new ones, so the check is useful before `git add` too."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "docs/"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return sorted(set(p for p in out.split("\n") if p.strip()))


def is_readme(path):
    return os.path.basename(path).lower() == "readme.md"


def mentioned(path, index_text):
    base = os.path.basename(path)
    stem, _ = os.path.splitext(base)
    if is_readme(path):
        parent = os.path.basename(os.path.dirname(path))
        return path in index_text or ("%s/README.md" % parent) in index_text
    # the interactive labs are listed by stem, without the .html
    return path in index_text or base in index_text or stem in index_text


def sectioned(path, index_text):
    return ("### `%s`" % path) in index_text


def main():
    index_text = io.open(INDEX, encoding="utf-8").read()
    files = docs_files()

    not_mentioned = [f for f in files if not mentioned(f, index_text)]
    needs_section = [f for f in files if f.endswith(".md") and not is_readme(f)]
    not_sectioned = [f for f in needs_section if not sectioned(f, index_text)]

    if not not_mentioned and not not_sectioned:
        print("OK  INDEX.md covers docs/ -- %d files mentioned, %d with their own section"
              % (len(files), len(needs_section)))
        return 0

    if not_mentioned:
        print("FAIL  %d file(s) under docs/ are not mentioned anywhere in INDEX.md:"
              % len(not_mentioned))
        for f in not_mentioned:
            print("        %s" % f)
        print("      Add a row or a section. If a file does not belong in the index,")
        print("      it probably does not belong in docs/ either.")
        print()

    if not_sectioned:
        print("FAIL  %d document(s) have no `### ` section of their own in INDEX.md:"
              % len(not_sectioned))
        for f in not_sectioned:
            print("        %s" % f)
            print("          expected a heading:  ### `%s`" % f)
        print("      A document named only in the topic tables is half-indexed: a")
        print("      reader can find it by topic but not learn what is in it.")

    return 1


if __name__ == "__main__":
    sys.exit(main())
