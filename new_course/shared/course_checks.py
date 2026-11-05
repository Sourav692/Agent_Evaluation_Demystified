"""Checks that keep each week's notebook and theory HTML in step with their sources.

Used by every week's tests:
- the notebook defines the same functions as lab.py, line for line (compared as syntax trees);
- the notebook runs top to bottom, skipping cells tagged `skip-execution`;
- the theory HTML equals a fresh render of the theory Markdown.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import sys
import types
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[1]


def notebook_code_cells(path: Path) -> list[tuple[str, list[str]]]:
    cells = json.loads(path.read_text())["cells"]
    return [("".join(c["source"]), c.get("metadata", {}).get("tags", []))
            for c in cells if c["cell_type"] == "code"]


def _definitions(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    return {node.name: ast.dump(node) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def notebook_drift(notebook: Path, lab: Path) -> list[str]:
    """Names defined in both files whose code differs. Empty means in step."""
    lab_defs = _definitions(lab.read_text())
    nb_defs = _definitions("\n\n".join(src for src, _tags in notebook_code_cells(notebook)))
    return sorted(name for name in nb_defs.keys() & lab_defs.keys() if nb_defs[name] != lab_defs[name])


def shared_definitions(notebook: Path, lab: Path) -> set[str]:
    lab_defs = _definitions(lab.read_text())
    nb_defs = _definitions("\n\n".join(src for src, _tags in notebook_code_cells(notebook)))
    return nb_defs.keys() & lab_defs.keys()


def run_notebook(path: Path) -> tuple[dict, str]:
    """Execute the notebook's code cells in one namespace. Returns (namespace, printed text)."""
    name = f"notebook_{path.stem.replace('-', '_')}"
    module = types.ModuleType(name)
    sys.modules[name] = module  # dataclasses look their module up here
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        for source, tags in notebook_code_cells(path):
            if "skip-execution" not in tags:
                exec(compile(source, str(path), "exec"), module.__dict__)
    return module.__dict__, printed.getvalue()


def html_is_fresh(markdown_path: Path) -> bool:
    sys.path.insert(0, str(COURSE_ROOT / "tools"))
    from build_html import render  # noqa: PLC0415  (needs the `markdown` package)

    return markdown_path.with_suffix(".html").read_text() == render(markdown_path)
