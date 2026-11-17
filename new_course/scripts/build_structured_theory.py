#!/usr/bin/env python3
"""Render the structured companions, preferring local HTML destinations in HTML."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

COURSE = Path(__file__).resolve().parents[1]
RENDERER = COURSE.parent / ".agents/skills/course-content/standalone/scripts/build_site.py"


def build():
    lessons = sorted(COURSE.glob("weeks/*/theory/*-theory-simplified-structured.md"))
    for source in lessons:
        def browser_destination(match):
            destination = match.group(1)
            path, separator, fragment = destination.partition("#")
            if path.endswith(".md") and (source.parent / path).with_suffix(".html").is_file():
                destination = path[:-3] + ".html" + separator + fragment
            return "](" + destination + ")"

        content = re.sub(r"\]\(([^)]+)\)", browser_destination, source.read_text())
        with tempfile.TemporaryDirectory(prefix="structured-theory-") as scratch:
            prepared = Path(scratch) / source.name
            prepared.write_text(content)
            subprocess.run(
                [sys.executable, str(RENDERER), str(prepared), str(source.with_suffix(".html"))],
                check=True,
            )


if __name__ == "__main__":
    build()
