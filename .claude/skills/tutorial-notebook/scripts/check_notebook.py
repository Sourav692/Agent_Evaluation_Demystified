"""Check a notebook against the tutorial-notebook format. Standard library only.

Usage: python3 check_notebook.py NOTEBOOK.ipynb [...]
Exits 1 if any notebook fails. Checks structure only, not teaching quality.
"""
import json
import re
import sys

BANNER = "# " + "=" * 76


def check(path):
    with open(path, encoding="utf-8") as f:
        cells = json.load(f)["cells"]
    problems = []
    sources = ["".join(cell["source"]) for cell in cells]
    markdown = [s for c, s in zip(cells, sources) if c["cell_type"] == "markdown"]

    title = markdown[0] if markdown else ""
    if not re.match(r"# \S+ \d{2} — ", title):
        problems.append("cell 0 must start '# <emoji> NN — <Title>'")
    for section in ("## Learning Objectives", "## Prerequisites"):
        if section not in title:
            problems.append(f"title cell is missing '{section}'")
    if not any("## 🗺️ The idea" in s for s in markdown):
        problems.append("no '## 🗺️ The idea' cell")
    if not any(re.search(r"^## ⚙️ Part 0: Setup", s, re.M) for s in markdown):
        problems.append("no '## ⚙️ Part 0: Setup' heading")

    summary = [s for s in markdown if "## 📝 Summary" in s]
    if not summary:
        problems.append("no '## 📝 Summary' cell")
    elif "### Next Steps" not in summary[-1]:
        problems.append("summary has no '### Next Steps'")
    if cells and cells[-1]["cell_type"] != "markdown":
        problems.append("last cell should be the markdown summary")

    ids = [cell.get("id") for cell in cells]
    if len(set(ids)) != len(ids):
        problems.append("cell IDs are not unique")
    for index, (cell, source) in enumerate(zip(cells, sources)):
        if cell["cell_type"] == "markdown" and index > 0:
            for match in re.finditer(r"^## ", source, re.M):
                if not source[: match.start()].rstrip().endswith("---"):
                    problems.append(f"cell {index}: '##' heading without '---' above it")
        if cell["cell_type"] == "code" and source.strip():
            lines = source.splitlines()
            if len(lines) < 3 or lines[0] != BANNER or lines[2] != BANNER or not lines[1].startswith("# "):
                problems.append(f"cell {index}: code cell does not start with a 3-line banner")
        outputs = json.dumps(cell.get("outputs", []))
        if "/Users/" in source or "/Users/" in outputs:
            problems.append(f"cell {index}: contains a machine path (/Users/...)")
    return problems


if __name__ == "__main__":
    failed = False
    for notebook_path in sys.argv[1:]:
        found = check(notebook_path)
        print(("FAIL " if found else "PASS ") + notebook_path)
        for problem in found:
            print("   - " + problem)
        failed = failed or bool(found)
    sys.exit(1 if failed else 0)
