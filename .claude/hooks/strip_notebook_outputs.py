#!/usr/bin/env python3
"""Clear outputs and execution_count on staged .ipynb files, then restage them.

Invoked by .git/hooks/pre-commit. Stdlib only — no nbconvert dependency.
Only rewrites a notebook when something actually changes, so clean commits are
untouched and mtimes stay stable.
"""
import json
import subprocess
import sys
from pathlib import Path

# Course 03's outputs are committed on purpose: its runs are paid, and readers
# who don't run them still see the results. Owner decision (Q4, 2026-10-15):
# keep them, with local paths scrubbed instead of the outputs stripped.
KEEP_OUTPUTS = ("courses/03-agentic-eval-harness/",)


def staged_notebooks(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return [root / p for p in out.stdout.split("\0") if p.endswith(".ipynb")]


def strip(nb_path: Path) -> bool:
    """Return True if the notebook was modified."""
    try:
        raw = nb_path.read_text(encoding="utf-8")
        nb = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"pre-commit: skipping unreadable notebook {nb_path.name}: {exc}")
        return False

    changed = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        elif "outputs" not in cell:
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True
        # Databricks leaves this behind; the format contract says drop it.
        meta = cell.get("metadata", {})
        if "application/vnd.databricks.v1+cell" in meta:
            del meta["application/vnd.databricks.v1+cell"]
            changed = True

    if not changed:
        return False

    # Match Jupyter's on-disk form: 1-space indent, trailing newline.
    nb_path.write_text(
        json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True


def main() -> int:
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    )

    cleaned = []
    for nb in staged_notebooks(root):
        if not nb.exists():
            continue
        if nb.relative_to(root).as_posix().startswith(KEEP_OUTPUTS):
            continue
        if strip(nb):
            subprocess.run(["git", "add", "--", str(nb)], cwd=root, check=True)
            cleaned.append(nb.relative_to(root))

    if cleaned:
        print("pre-commit: cleared notebook outputs in:")
        for p in cleaned:
            print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
