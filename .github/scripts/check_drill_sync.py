#!/usr/bin/env python3
"""Fail when the question bank changes and the drill page does not.

`docs/interview-prep/QUESTION_BANK.md` is canonical; `evaluation-round-drill.html`
carries the same 35 questions and 19 cases in a quiz format. They are two thirds
phrase-identical and maintained by hand, and four commits have already changed
one without the other -- 5e0dc89 exists to repair that.

The drill records the bank's content hash in an HTML comment. This recomputes it
and compares. Stdlib only; no network, no cost.

    python3 .github/scripts/check_drill_sync.py            # check  (CI)
    python3 .github/scripts/check_drill_sync.py --update   # re-sync after editing both
"""
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANK = os.path.join(ROOT, "docs", "interview-prep", "QUESTION_BANK.md")
DRILL = os.path.join(ROOT, "docs", "interview-prep", "evaluation-round-drill.html")

MARKER = re.compile(r"<!-- built-from: QUESTION_BANK\.md sha256:([0-9a-f]{64}) -->")


def bank_hash():
    """Hash the bank's content, ignoring trailing whitespace and line endings.

    Normalising means a whitespace-only commit does not trip the check, while
    any real edit does.
    """
    text = io.open(BANK, encoding="utf-8").read()
    lines = [l.rstrip() for l in text.replace("\r\n", "\n").split("\n")]
    body = "\n".join(lines).strip()
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def read_recorded(drill_text):
    m = MARKER.search(drill_text)
    return m.group(1) if m else None


def update():
    text = io.open(DRILL, encoding="utf-8").read()
    stamp = "<!-- built-from: QUESTION_BANK.md sha256:%s -->" % bank_hash()
    if MARKER.search(text):
        text = MARKER.sub(stamp, text, count=1)
    else:
        # first run: put it directly after the opening <html ...> tag
        m = re.search(r"<html[^>]*>", text)
        at = m.end() if m else 0
        text = text[:at] + "\n" + stamp + text[at:]
    io.open(DRILL, "w", encoding="utf-8").write(text)
    print("✅ recorded QUESTION_BANK.md sha256:%s in the drill" % bank_hash()[:16])


def check():
    text = io.open(DRILL, encoding="utf-8").read()
    recorded = read_recorded(text)
    actual = bank_hash()

    if recorded is None:
        print("❌ the drill carries no provenance marker.")
        print("   Run: python3 .github/scripts/check_drill_sync.py --update")
        return 1

    if recorded == actual:
        print("✅ drill is in sync with QUESTION_BANK.md (sha256:%s)" % actual[:16])
        return 0

    print("❌ QUESTION_BANK.md has changed and the drill has not been re-synced.")
    print()
    print("   bank now  : sha256:%s" % actual[:16])
    print("   drill says: sha256:%s" % recorded[:16])
    print()
    print("   The bank is canonical. If your change belongs in the quiz too, edit")
    print("   docs/interview-prep/evaluation-round-drill.html to match, then run:")
    print("     python3 .github/scripts/check_drill_sync.py --update")
    print()
    print("   If it genuinely does not belong in the quiz -- a heading, a link, a")
    print("   typo -- run --update on its own to record that you checked.")
    return 1


if __name__ == "__main__":
    sys.exit(update() or 0 if "--update" in sys.argv else check())
