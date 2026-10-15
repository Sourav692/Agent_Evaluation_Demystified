#!/usr/bin/env python3
"""Write site/page-dates.json: the last-changed date of every published page.

Vercel's build has no usable git history, so dates can't be computed there.
They are computed here, where git exists, and committed. The footer, the
sitemap's lastmod and the JSON-LD dateModified all read the manifest.

    python3 site/stamp_dates.py            rewrite the manifest from git log
    python3 site/stamp_dates.py --staged   same, but staged files get today's
                                           date (the pre-commit hook uses this)
    python3 site/stamp_dates.py --check    exit 1 if any entry is stale (CI)
    python3 site/stamp_dates.py --self-test

Stdlib only. The published set comes from build.py, so it can't drift.
"""
import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import COPY, RENDER, ROOT  # noqa: E402

MANIFEST = os.path.join(ROOT, "site", "page-dates.json")


def published():
    """Repo paths of every page the site builds from docs/."""
    srcs = [s for g in RENDER.values() for s, *_ in g] + [s for g in COPY.values() for s, *_ in g]
    return sorted("docs/" + s for s in srcs)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def last_changed(path):
    """Committer date (YYYY-MM-DD) of the last commit touching path, or None."""
    return git("log", "-1", "--format=%cs", "--", path).strip() or None


def actual_dates(staged=False):
    today = datetime.date.today().isoformat()
    in_index = set(git("diff", "--cached", "--name-only").split("\n")) if staged else set()
    return {p: today if p in in_index else last_changed(p) or today for p in published()}


def stale(manifest, actual):
    """Paths whose manifest date is missing or wrong, plus entries no longer published."""
    return sorted({p for p, d in actual.items() if manifest.get(p) != d}
                  | (set(manifest) - set(actual)))


def self_test():
    assert stale({"a": "2026-01-01"}, {"a": "2026-01-01"}) == []
    assert stale({"a": "2026-01-01"}, {"a": "2026-01-02"}) == ["a"]
    assert stale({}, {"a": "2026-01-01"}) == ["a"]
    assert stale({"gone": "2026-01-01"}, {}) == ["gone"]
    print("self-test ok")


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        try:
            manifest = json.load(open(MANIFEST, encoding="utf-8"))
        except FileNotFoundError:
            manifest = {}
        bad = stale(manifest, actual_dates())
        if bad:
            sys.exit("site/page-dates.json is stale for:\n   %s\n"
                     "Run: python3 site/stamp_dates.py  and commit the result."
                     % "\n   ".join(bad))
        print("page-dates.json is current (%d pages)" % len(manifest))
        return
    dates = actual_dates(staged="--staged" in argv)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(dates, f, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
