#!/usr/bin/env python3
"""Validate an implementation plan written by the site-plan skill.

Parses the markdown plan, extracts every task table, phase and traceability row,
and reports structural problems. Prints a human summary, or JSON with --json.

Usage: python3 check_plan.py PLAN.md [--json]
Exit code: 0 if no errors (warnings allowed), 1 if errors, 2 on bad input.
"""
import json
import re
import sys
from collections import defaultdict

EXPECTED_SECTIONS = {
    0: "Summary",
    1: "Inputs, mode and assumptions",
    2: "Current state",
    3: "Product goals, users and success metrics",
    4: "Information architecture and sitemap",
    5: "UX flows and key screens",
    6: "Visual design system",
    7: "Component inventory",
    8: "Frontend architecture",
    9: "Backend, data and APIs",
    10: "Content and CMS pipeline",
    11: "Accessibility, performance and SEO",
    12: "Security, privacy and compliance",
    13: "Testing, deployment and operations",
    14: "Phased roadmap",
    15: "Risks and open questions",
    16: "Appendix: requirement traceability",
}
FOUR_PART_SECTIONS = range(3, 14)
FOUR_PARTS = ["Goal", "Decisions", "Tasks", "Acceptance criteria"]
VALID_SIZES = {"S", "M", "L"}
TASK_ID = re.compile(r"\b([A-Z][A-Z0-9]{1,5}-\d{1,3})\b")
SECTION_H2 = re.compile(r"^##\s+(\d{1,2})\.\s+(.*)$")
PHASE_H3 = re.compile(r"^###\s+Phase\s+(\d+)\s*[:.\-]?\s*(.*)$", re.I)


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def is_separator(line):
    return bool(re.match(r"^\s*\|?\s*:?-{3,}", line))


def parse_tables(lines):
    """Yield (start_line_no, header_cells, rows) for each markdown table."""
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            header = split_row(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, split_row(lines[j])))
                j += 1
            yield i + 1, header, rows
            i = j
        else:
            i += 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    try:
        text = open(args[0], encoding="utf-8").read()
    except OSError as e:
        print(f"cannot read plan: {e}", file=sys.stderr)
        sys.exit(2)
    lines = text.splitlines()

    errors, warnings = [], []

    # Sections: map line ranges to section numbers.
    sections = {}  # num -> (title, start, end)
    starts = []
    for idx, line in enumerate(lines):
        m = SECTION_H2.match(line)
        if m:
            starts.append((idx, int(m.group(1)), m.group(2).strip()))
    for k, (idx, num, title) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        sections[num] = (title, idx, end)

    def section_of(line_no):
        for num, (_, s, e) in sections.items():
            if s < line_no <= e:
                return num
        return None

    for num, title in EXPECTED_SECTIONS.items():
        if num not in sections:
            errors.append(f"missing section {num}. {title}")

    for num in FOUR_PART_SECTIONS:
        if num not in sections:
            continue
        _, s, e = sections[num]
        body = "\n".join(lines[s:e])
        if re.search(r"out of scope|not applicable|does not apply|no backend", body, re.I) and len(body) < 600:
            continue  # honestly skipped section
        for part in FOUR_PARTS:
            if not re.search(rf"\*\*{part}\b", body):
                warnings.append(f"section {num}: missing **{part}.** part")

    # Tasks.
    tasks = {}
    for start, header, rows in parse_tables(lines):
        h = [c.lower() for c in header]
        if not (h and h[0] == "id" and any("outcome" in c for c in h)):
            continue
        col = {name: next((k for k, c in enumerate(h) if name in c), None)
               for name in ("outcome", "size", "depends")}
        for line_no, cells in rows:
            tid = cells[0].strip("` ")
            if not TASK_ID.fullmatch(tid):
                warnings.append(f"line {line_no}: task ID '{tid}' does not match PREFIX-NN")
                continue
            get = lambda k: cells[col[k]] if col[k] is not None and col[k] < len(cells) else ""
            deps_raw = get("depends")
            deps = TASK_ID.findall(deps_raw)
            task = {
                "id": tid,
                "outcome": get("outcome"),
                "size": get("size").strip("` ").upper(),
                "depends_on": deps,
                "section": section_of(line_no),
                "line": line_no,
            }
            if tid in tasks:
                errors.append(f"duplicate task ID {tid} (lines {tasks[tid]['line']} and {line_no})")
                continue
            tasks[tid] = task
            if task["size"] not in VALID_SIZES:
                errors.append(f"{tid}: size '{task['size']}' is not S, M or L (split anything larger)")
            if len(task["outcome"].split()) < 4:
                warnings.append(f"{tid}: outcome '{task['outcome']}' is too vague to build from")

    if not tasks:
        errors.append("no task tables found (expected | ID | Outcome | Size | Depends on |)")

    for t in tasks.values():
        for d in t["depends_on"]:
            if d not in tasks:
                errors.append(f"{t['id']}: depends on unknown task {d}")
            elif d == t["id"]:
                errors.append(f"{t['id']}: depends on itself")

    # Cycle detection and topological order (Kahn).
    indeg = {tid: 0 for tid in tasks}
    children = defaultdict(list)
    for t in tasks.values():
        for d in t["depends_on"]:
            if d in tasks and d != t["id"]:
                indeg[t["id"]] += 1
                children[d].append(t["id"])
    queue = sorted(tid for tid, n in indeg.items() if n == 0)
    order = []
    while queue:
        tid = queue.pop(0)
        order.append(tid)
        for c in sorted(children[tid]):
            indeg[c] -= 1
            if indeg[c] == 0:
                queue.append(c)
    cyclic = sorted(tid for tid in tasks if tid not in order)
    if cyclic:
        errors.append(f"dependency cycle among: {', '.join(cyclic)}")

    # Phases.
    phases = []
    current = None
    for idx, line in enumerate(lines):
        m = PHASE_H3.match(line)
        if m:
            current = {"number": int(m.group(1)), "name": m.group(2).strip(), "tasks": [],
                       "outcome": "", "exit_criteria": [], "line": idx + 1}
            phases.append(current)
            continue
        if current is None:
            continue
        if line.startswith("## ") or line.startswith("### "):
            current = None
            continue
        if re.match(r"^\s*Tasks?\s*:", line, re.I):
            current["tasks"].extend(TASK_ID.findall(line))
        elif re.match(r"^\s*Outcome\s*:", line, re.I):
            current["outcome"] = line.split(":", 1)[1].strip()
        elif current["tasks"] and re.match(r"^\s*-\s+", line):
            current["exit_criteria"].append(line.strip()[2:].strip())

    if not phases:
        errors.append("no phases found (expected '### Phase N: name' under section 14)")

    phase_of = {}
    for p in phases:
        if not p["tasks"]:
            errors.append(f"Phase {p['number']} lists no tasks")
        if not p["exit_criteria"]:
            warnings.append(f"Phase {p['number']} has no exit criteria")
        for tid in p["tasks"]:
            if tid not in tasks:
                errors.append(f"Phase {p['number']} references unknown task {tid}")
            elif tid in phase_of:
                errors.append(f"{tid} is in Phase {phase_of[tid]} and Phase {p['number']}")
            else:
                phase_of[tid] = p["number"]

    unphased = sorted(tid for tid in tasks if tid not in phase_of)
    if unphased:
        warnings.append(f"tasks in no phase (backlog): {', '.join(unphased)}")

    for t in tasks.values():
        for d in t["depends_on"]:
            if t["id"] in phase_of and d in phase_of and phase_of[d] > phase_of[t["id"]]:
                errors.append(f"{t['id']} (Phase {phase_of[t['id']]}) depends on {d} "
                              f"from later Phase {phase_of[d]}")

    # Traceability.
    trace = []
    for start, header, rows in parse_tables(lines):
        h = [c.lower() for c in header]
        if h and h[0].startswith("requirement"):
            tcol = next((k for k, c in enumerate(h) if "task" in c), None)
            for line_no, cells in rows:
                ids = TASK_ID.findall(cells[tcol]) if tcol is not None and tcol < len(cells) else []
                trace.append({"requirement": cells[0], "tasks": ids, "line": line_no})
                if not ids:
                    reason = cells[-1] if len(cells) > 1 else ""
                    warnings.append(f"requirement {cells[0]} maps to no task"
                                    + (f" (note: {reason})" if reason else ""))
                for tid in ids:
                    if tid not in tasks:
                        errors.append(f"requirement {cells[0]} maps to unknown task {tid}")

    for t in tasks.values():
        t["phase"] = phase_of.get(t["id"])

    result = {
        "plan": args[0],
        "sections_found": sorted(sections),
        "task_count": len(tasks),
        "phases": phases,
        "tasks": [tasks[tid] for tid in order] + [tasks[tid] for tid in cyclic],
        "build_order": order,
        "traceability": trace,
        "errors": errors,
        "warnings": warnings,
    }

    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Plan: {args[0]}")
        print(f"Sections: {len(sections)}/17  Tasks: {len(tasks)}  Phases: {len(phases)}")
        for p in phases:
            print(f"  Phase {p['number']} {p['name']}: {len(p['tasks'])} tasks")
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
