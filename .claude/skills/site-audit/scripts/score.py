#!/usr/bin/env python3
"""Score a site audit and track it over time, for one site profile.

Standard library only. Every subcommand takes --profile <name> (a folder under
profiles/: fde, eval). The profile's profile.json names the own site, the
competitors and the dimension labels, and optionally a bundled baseline
(for seed) or first-audit defaults (start, for new on an empty history).

Subcommands:

  seed    Start a history file from the profile's bundled baseline (only
          profiles that have one, e.g. fde). Safe to repeat.
  new     Start a new scores.json. From the latest audit when the history has
          one (scores carried forward, every check reset to not_checked);
          from the profile's start file when it is empty (scores left blank).
  report  Validate a scores.json, compute averages and check pass rates,
          compare with the previous audit in the history, write a markdown
          summary, and (with --append) add the audit to the history.
  trend   Print every audit in the history as one table.

Examples:
  python3 score.py --profile fde seed --history .website_spec/site-audits/history.jsonl
  python3 score.py --profile eval new --history .website_spec/site-audits/history.jsonl --date 2026-11-20 \
      --out .website_spec/site-audits/2026-11-20/scores.json
  python3 score.py --profile eval report --scores .website_spec/site-audits/2026-11-20/scores.json \
      --history .website_spec/site-audits/history.jsonl --out .website_spec/site-audits/2026-11-20/score-summary.md
  python3 score.py --profile eval report ... --append          # record it once the report is written
  python3 score.py --profile eval trend --history .website_spec/site-audits/history.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILES = SKILL_DIR / "profiles"

CONTENT = ["coverage", "depth", "practice", "grounding", "credibility"]
STRUCTURE = ["navigation", "onboarding", "template", "progress", "polish"]
DIMS = CONTENT + STRUCTURE
LABELS = {
    "coverage": "Coverage",
    "depth": "Depth",
    "practice": "Practice and feedback",
    "grounding": "Grounding",
    "credibility": "Credibility and freshness",
    "navigation": "Navigation and IA",
    "onboarding": "Onboarding",
    "template": "Page template",
    "progress": "Progress",
    "polish": "Polish and trust",
}
# Set from the profile by load_profile().
SITE_NAMES: dict[str, str] = {}
OWN = ""
PROFILE: dict = {}
STATUSES = {"pass": 1.0, "partial": 0.5, "fail": 0.0, "na": None, "not_checked": None}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------- helpers
def load_profile(name: str) -> dict:
    """Read profiles/<name>/profile.json and set OWN, SITE_NAMES and LABELS."""
    global OWN, SITE_NAMES, PROFILE
    pdir = PROFILES / name
    if not (pdir / "profile.json").exists():
        known = sorted(p.name for p in PROFILES.iterdir() if (p / "profile.json").exists())
        raise SystemExit(f"Unknown profile {name!r}; use one of {known}.")
    PROFILE = json.loads((pdir / "profile.json").read_text(encoding="utf-8"))
    PROFILE["dir"] = pdir
    OWN = PROFILE["own"]
    SITE_NAMES = PROFILE["site_names"]
    LABELS.update(PROFILE.get("labels", {}))
    return PROFILE


def profile_file(key: str) -> str | None:
    """Absolute path of an optional profile file (baseline, start), or None."""
    rel = PROFILE.get(key)
    return str(PROFILE["dir"] / rel) if rel else None


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return sorted(entries, key=lambda e: e["date"])


def write_history(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for e in sorted(entries, key=lambda e: e["date"]):
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def site_name(key: str) -> str:
    return SITE_NAMES.get(key, key)


def fmt(x: float | None, nd: int = 1) -> str:
    if x is None or x != x:  # None or NaN
        return "-"
    return f"{x:.{nd}f}"


def fmt_delta(x: float | None, nd: int = 1) -> str:
    if x is None or x != x:
        return "-"
    if abs(x) < 10 ** (-nd) / 2:
        return "0"
    return f"{x:+.{nd}f}"


# ---------------------------------------------------------------- validation
def validate_catalog(catalog: dict) -> list[str]:
    """Problems in data/checks.json itself (e.g. a newly added check with a typo)."""
    problems, seen = [], set()
    lenses = set(catalog.get("lenses", {}))
    for c in catalog.get("checks", []):
        cid = c.get("id", "?")
        if cid in seen:
            problems.append(f"catalogue: duplicate check ID {cid}")
        seen.add(cid)
        if c.get("lens") not in lenses:
            problems.append(f"catalogue: {cid} has lens {c.get('lens')!r}, not one of {sorted(lenses)}")
        elif not cid.startswith(c["lens"] + "-"):
            problems.append(f"catalogue: {cid} does not start with its lens {c['lens']}-")
        if c.get("dimension") not in DIMS:
            problems.append(f"catalogue: {cid} has dimension {c.get('dimension')!r}, not one of {DIMS}")
        if c.get("severity") not in SEVERITY_ORDER:
            problems.append(f"catalogue: {cid} has severity {c.get('severity')!r}")
    for gid, g in catalog.get("gaps", {}).items():
        for cid in g.get("checks", []):
            if cid not in seen:
                problems.append(f"catalogue: gap {gid} refers to unknown check {cid}")
    return problems


def validate(audit: dict, catalog: dict) -> tuple[list[str], list[str]]:
    """Return (fatal, warnings).

    Fatal problems make the audit unusable (the report cannot be computed);
    warnings make it incomplete. --force can report past warnings, never past
    fatal problems, and the history is only updated when both lists are empty.
    """
    fatal, warn = validate_catalog(catalog), []
    for key in ("date", "site", "scores", "checks"):
        if key not in audit:
            fatal.append(f"missing top-level key '{key}'")
    if fatal:
        return fatal, warn
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(audit["date"])):
        fatal.append(f"date {audit['date']!r} is not YYYY-MM-DD")
    if not isinstance(audit["scores"], dict) or OWN not in audit["scores"]:
        fatal.append(f"scores.{OWN} is missing")
        return fatal, warn
    for site, dims in audit["scores"].items():
        if not isinstance(dims, dict):
            fatal.append(f"scores.{site} is not an object of dimension scores")
            continue
        for d in DIMS:
            v = dims.get(d)
            if v is None:
                fatal.append(f"scores.{site}.{d} is missing")
            elif not isinstance(v, (int, float)) or not 1 <= v <= 10:
                fatal.append(f"scores.{site}.{d} = {v!r} is not a number from 1 to 10")
    if not isinstance(audit["checks"], dict):
        fatal.append("checks is not an object keyed by check ID")
        return fatal, warn
    known = {c["id"] for c in catalog["checks"]}
    for cid, res in audit["checks"].items():
        if not isinstance(res, dict):
            fatal.append(f"check {cid} must be an object like {{\"status\": \"pass\", \"evidence\": \"...\"}}")
            continue
        if res.get("status") not in STATUSES:
            fatal.append(f"check {cid} has status {res.get('status')!r}; use one of {sorted(STATUSES)}")
        elif res["status"] in ("fail", "partial") and not res.get("evidence"):
            warn.append(f"check {cid} is {res['status']} but has no evidence")
        if cid not in known:
            warn.append(f"check {cid} is not in the catalogue (add it to data/checks.json first)")
    missing = sorted(known - set(audit["checks"]))
    if missing:
        warn.append("checks not recorded (use not_checked if skipped): " + ", ".join(missing))
    return fatal, warn


# ---------------------------------------------------------------- metrics
def site_metrics(dims: dict) -> dict:
    c = avg([dims[d] for d in CONTENT])
    s = avg([dims[d] for d in STRUCTURE])
    return {"content": c, "structure": s, "overall": (c + s) / 2}


def ranks(audit: dict) -> dict:
    metrics = {k: site_metrics(v) for k, v in audit["scores"].items()}
    out = {}
    for m in ("content", "structure", "overall"):
        order = sorted(metrics, key=lambda k: -metrics[k][m])
        # competition ranking: ties share the better rank
        r, prev, result = 0, None, {}
        for i, k in enumerate(order, 1):
            if metrics[k][m] != prev:
                r, prev = i, metrics[k][m]
            result[k] = r
        out[m] = result
    return {"metrics": metrics, "ranks": out, "n": len(metrics)}


def check_rates(audit: dict, catalog: dict) -> dict:
    lens_of = {c["id"]: c["lens"] for c in catalog["checks"]}
    by_lens: dict[str, list[float]] = {}
    counts = {s: 0 for s in STATUSES}
    for cid, res in audit["checks"].items():
        st = res.get("status")
        counts[st] = counts.get(st, 0) + 1
        pts = STATUSES.get(st)
        if pts is None:
            continue
        by_lens.setdefault(lens_of.get(cid, cid[:2]), []).append(pts)
    all_pts = [p for v in by_lens.values() for p in v]
    return {
        "by_lens": {k: avg(v) for k, v in sorted(by_lens.items())},
        "overall": avg(all_pts),
        "counts": counts,
        "assessed": len(all_pts),
    }


def compare_checks(cur: dict, prev: dict | None) -> dict:
    """Classify each check's movement since the previous audit.

    Only moves between assessed statuses (fail / partial / pass) count as fixed,
    improved or regressed. Moves into or out of na / not_checked are reported
    separately, because they reflect what was assessed, not a change in the site.
    """
    out = {"fixed": [], "improved": [], "regressed": [], "newly_assessed": [], "not_assessed": [],
           "new": [], "removed": [], "unchanged_fail": []}
    if not prev:
        return out
    pc, cc = prev.get("checks", {}), cur["checks"]
    rank = {"fail": 0, "partial": 1, "pass": 2}
    for cid, res in cc.items():
        st = res.get("status")
        if cid not in pc:
            out["new"].append(cid)
            continue
        old = pc[cid].get("status")
        if old in rank and st in rank:
            if rank[st] > rank[old]:
                out["fixed" if st == "pass" else "improved"].append((cid, old, st))
            elif rank[st] < rank[old]:
                out["regressed"].append((cid, old, st))
            elif st in ("fail", "partial"):
                out["unchanged_fail"].append(cid)
        elif st in rank and old not in rank:
            out["newly_assessed"].append((cid, old, st))
        elif old in rank and st not in rank:
            out["not_assessed"].append((cid, old, st))
    out["removed"] = sorted(set(pc) - set(cc))
    return out


def shared_rate(cur: dict, prev: dict | None) -> tuple[float, float, int] | None:
    """Pass rate of both audits over the checks assessed in both: the like-for-like number."""
    if not prev:
        return None
    a, b = [], []
    for cid, res in cur["checks"].items():
        p = prev.get("checks", {}).get(cid, {})
        x, y = STATUSES.get(res.get("status")), STATUSES.get(p.get("status"))
        if x is not None and y is not None:
            a.append(x)
            b.append(y)
    return (avg(a), avg(b), len(a)) if a else None


def previous_entry(history: list[dict], date: str) -> dict | None:
    earlier = [e for e in history if e["date"] < date]
    return earlier[-1] if earlier else None


# ---------------------------------------------------------------- report
def build_summary(audit: dict, prev: dict | None, catalog: dict) -> str:
    cat = {c["id"]: c for c in catalog["checks"]}
    lenses = catalog["lenses"]
    r = ranks(audit)
    m = r["metrics"][OWN]
    pm = site_metrics(prev["scores"][OWN]) if prev else None
    rates = check_rates(audit, catalog)
    prates = check_rates(prev, catalog) if prev else None
    diff = compare_checks(audit, prev)
    own = audit["scores"][OWN]
    targets = audit.get("targets") or (prev or {}).get("targets") or {}
    lines = []
    lines.append(f"# Score summary — {audit['date']}")
    lines.append("")
    lines.append(f"Site: {audit['site']}  ")
    lines.append(f"Compared with: {prev['date'] if prev else 'no earlier audit'}")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    n = r["n"]
    lines.append(
        f"- Overall **{fmt(m['overall'])}** ({fmt_delta(m['overall'] - pm['overall']) if pm else '-'} vs last), "
        f"rank {r['ranks']['overall'][OWN]} of {n}"
    )
    lines.append(
        f"- Content **{fmt(m['content'])}** ({fmt_delta(m['content'] - pm['content']) if pm else '-'}), "
        f"rank {r['ranks']['content'][OWN]} of {n}"
    )
    lines.append(
        f"- Structure **{fmt(m['structure'])}** ({fmt_delta(m['structure'] - pm['structure']) if pm else '-'}), "
        f"rank {r['ranks']['structure'][OWN]} of {n}"
    )
    c = rates["counts"]
    lines.append(
        f"- Check pass rate **{fmt(rates['overall'] * 100, 0)}%** over {rates['assessed']} assessed checks "
        f"({c.get('not_checked', 0)} not checked, {c.get('na', 0)} n/a)"
    )
    sr = shared_rate(audit, prev)
    if sr:
        lines.append(
            f"- Like-for-like pass rate (the {sr[2]} checks assessed in both audits): "
            f"**{fmt(sr[0] * 100, 0)}%** vs {fmt(sr[1] * 100, 0)}% last time ({fmt_delta((sr[0] - sr[1]) * 100, 0)} pts). "
            "Use this number for progress; the plain pass rate also moves when coverage changes."
        )
    lines.append("")

    lines.append(f"## Dimension scores ({site_name(OWN)})")
    lines.append("")
    lines.append("| Dimension | Group | Score | Previous | Change | Target | Gap to target |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for d in DIMS:
        prev_v = prev["scores"][OWN][d] if prev else None
        t = targets.get(d)
        lines.append(
            f"| {LABELS[d]} | {'Content' if d in CONTENT else 'Structure'} | {own[d]} | "
            f"{prev_v if prev_v is not None else '-'} | "
            f"{fmt_delta(own[d] - prev_v, 0) if prev_v is not None else '-'} | "
            f"{t if t is not None else '-'} | {fmt_delta(own[d] - t, 0) if t is not None else '-'} |"
        )
    lines.append("")

    lines.append("## All sites")
    lines.append("")
    lines.append("| Site | Content | Structure | Overall | Scores as of |")
    lines.append("| --- | --- | --- | --- | --- |")
    asof = audit.get("scores_as_of", {})
    for k in sorted(r["metrics"], key=lambda k: -r["metrics"][k]["overall"]):
        mm = r["metrics"][k]
        name = f"**{site_name(k)}**" if k == OWN else site_name(k)
        lines.append(
            f"| {name} | {fmt(mm['content'])} | {fmt(mm['structure'])} | {fmt(mm['overall'])} | "
            f"{audit['date'] if k == OWN else asof.get(k, '-')} |"
        )
    lines.append("")

    lines.append("## Check pass rate by lens")
    lines.append("")
    lines.append("| Lens | Pass rate | Previous | Change |")
    lines.append("| --- | --- | --- | --- |")
    for lens, rate in rates["by_lens"].items():
        p = prates["by_lens"].get(lens) if prates else None
        lines.append(
            f"| {lens} {lenses.get(lens, {}).get('name', '')} | {fmt(rate * 100, 0)}% | "
            f"{fmt(p * 100, 0) + '%' if p is not None else '-'} | "
            f"{fmt_delta((rate - p) * 100, 0) + ' pts' if p is not None else '-'} |"
        )
    lines.append("")
    lines.append(
        f"Counts: {c.get('pass', 0)} pass, {c.get('partial', 0)} partial, {c.get('fail', 0)} fail, "
        f"{c.get('na', 0)} n/a, {c.get('not_checked', 0)} not checked."
    )
    lines.append("")

    def check_line(cid: str, extra: str = "") -> str:
        info = cat.get(cid, {})
        ev = audit["checks"].get(cid, {}).get("evidence", "")
        return f"- **{cid}** {info.get('title', '')} ({info.get('severity', '?')}){extra} — {ev}"

    if prev:
        lines.append("## Movement since last audit")
        lines.append("")
        for label, key in (("Fixed", "fixed"), ("Improved", "improved"), ("Regressed", "regressed")):
            items = diff[key]
            lines.append(f"### {label} ({len(items)})")
            lines.append("")
            if not items:
                lines.append("- none")
            for cid, old, new in sorted(items, key=lambda t: SEVERITY_ORDER.get(cat.get(t[0], {}).get("severity"), 9)):
                lines.append(check_line(cid, f": {old} → {new}"))
            lines.append("")
        for label, key in (("Newly assessed (was n/a or not checked)", "newly_assessed"),
                           ("Not assessed this time (was assessed)", "not_assessed")):
            if diff[key]:
                lines.append(f"### {label} ({len(diff[key])})")
                lines.append("")
                for cid, old, new in diff[key]:
                    lines.append(check_line(cid, f": {old} → {new}"))
                lines.append("")
        if diff["new"]:
            lines.append(f"### New checks ({len(diff['new'])})")
            lines.append("")
            for cid in diff["new"]:
                lines.append(check_line(cid, f": {audit['checks'][cid]['status']}"))
            lines.append("")
        if diff["removed"]:
            lines.append("### Checks no longer recorded")
            lines.append("")
            lines.append("- " + ", ".join(diff["removed"]))
            lines.append("")

    open_items = [cid for cid, res in audit["checks"].items() if res["status"] in ("fail", "partial")]
    open_items.sort(key=lambda cid: (SEVERITY_ORDER.get(cat.get(cid, {}).get("severity"), 9), cid))
    lines.append(f"## Still open ({len(open_items)})")
    lines.append("")
    for cid in open_items:
        lines.append(check_line(cid, f": {audit['checks'][cid]['status']}"))
    lines.append("")

    gaps = catalog.get("gaps", {})
    if gaps:
        lines.append("## Gap register")
        lines.append("")
        lines.append("| Gap | Title | Passing / checks | Not assessed | Status |")
        lines.append("| --- | --- | --- | --- | --- |")
        for gid, g in gaps.items():
            sts = [audit["checks"].get(cid, {}).get("status") for cid in g["checks"]]
            assessed = [s for s in sts if s in ("pass", "partial", "fail")]
            unassessed = len(sts) - len(assessed)
            passing = sum(1 for s in assessed if s == "pass")
            if not assessed:
                status = "Not assessed"
            elif passing == len(sts):
                status = "Closed"
            elif passing == len(assessed) and unassessed:
                status = "Passing so far (not all checks assessed)"
            elif passing or any(s == "partial" for s in assessed):
                status = "In progress"
            else:
                status = "Open"
            lines.append(f"| {gid} | {g['title']} | {passing}/{len(sts)} | {unassessed} | {status} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- commands
def cmd_seed(args) -> int:
    if not args.baseline:
        print("This profile has no bundled baseline; start with `new` instead.", file=sys.stderr)
        return 1
    hist = Path(args.history)
    entries = load_history(hist)
    base = load_json(Path(args.baseline))
    if any(e["date"] == base["date"] for e in entries):
        print(f"History already has an entry for {base['date']}; nothing to do.")
        return 0
    entries.append(base)
    write_history(hist, entries)
    print(f"Seeded {hist} with the {base['date']} baseline ({len(entries)} entries).")
    return 0


def cmd_new(args) -> int:
    """Start a new scores.json: scores, targets and competitor dates carried
    forward from the latest audit; every check reset to not_checked. With an
    empty history this is the first audit: own scores start blank (null) and
    report refuses the file until every one is filled in."""
    catalog = load_json(Path(args.catalog))
    history = load_history(Path(args.history))
    if history:
        last = history[-1]
    elif not args.start:
        print("History is empty. Run: score.py --profile <name> seed --history <file>", file=sys.stderr)
        return 1
    else:
        start = load_json(Path(args.start))
        last = {"date": "0000-00-00", "site": start["site"], "targets": start["targets"],
                "scores": {OWN: {d: None for d in DIMS}}, "scores_as_of": {}}
    if args.date <= last["date"] and not args.replace:
        print(f"The latest audit is dated {last['date']}; the new one must be later (or pass --replace).", file=sys.stderr)
        return 2
    new = {
        "date": args.date,
        "site": args.site or last["site"],
        "auditor": args.auditor,
        "notes": "",
        "docs": {},
        "scores": json.loads(json.dumps(last["scores"])),
        "scores_as_of": dict(last.get("scores_as_of", {})),
        "targets": dict(last.get("targets", {})),
        "rationale": {},
        "previous": {"date": last["date"]} if history else None,
        "checks": {c["id"]: {"status": "not_checked", "evidence": ""} for c in catalog["checks"]},
    }
    out = Path(args.out)
    if out.exists() and not args.replace:
        print(f"{out} already exists; pass --replace to overwrite it.", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    origin = f"scores carried forward from {last['date']}" if history else "first audit, scores blank (fill every one)"
    print(f"Wrote {out}: {origin}, {len(new['checks'])} checks set to not_checked.")
    return 0


def cmd_report(args) -> int:
    catalog = load_json(Path(args.catalog))
    audit = load_json(Path(args.scores))
    fatal, warn = validate(audit, catalog)
    if fatal or warn:
        print("scores.json has problems:", file=sys.stderr)
        for p in fatal:
            print("  - [must fix] " + p, file=sys.stderr)
        for p in warn:
            print("  - " + p, file=sys.stderr)
    if fatal:
        print("Fix the [must fix] items; the report cannot be computed without them.", file=sys.stderr)
        return 2
    if warn and not args.force:
        print("Fix them, or pass --force to see the report anyway (the history is never updated with --force).", file=sys.stderr)
        return 2
    hist_path = Path(args.history)
    history = load_history(hist_path)
    exists = any(e["date"] == audit["date"] for e in history)
    if args.append and exists and not args.replace:
        print(f"The history already has an audit dated {audit['date']}. Did you forget to change 'date' in "
              f"scores.json? To overwrite that audit on purpose, add --replace.", file=sys.stderr)
        return 2
    prev = previous_entry(history, audit["date"])
    summary = build_summary(audit, prev, catalog)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(summary + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(summary)
    if args.append:
        if warn:
            print("History not updated: scores.json still has problems (see above).", file=sys.stderr)
            return 2
        history = [e for e in history if e["date"] != audit["date"]] + [audit]
        write_history(hist_path, history)
        print(f"{'Replaced' if exists else 'Appended'} {audit['date']} in {hist_path}")
    return 0


def cmd_trend(args) -> int:
    catalog = load_json(Path(args.catalog))
    history = load_history(Path(args.history))
    if not history:
        hint = " Run seed first." if PROFILE.get("baseline") else ""
        print(f"History is empty: no audit has been recorded yet.{hint}")
        return 1
    print("| Date | Content | Structure | Overall | Pass rate | Like-for-like vs previous | Assessed | Not checked | Fails | Partials |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    prev = None
    for e in history:
        m = site_metrics(e["scores"][OWN])
        rates = check_rates(e, catalog)
        c = rates["counts"]
        sr = shared_rate(e, prev)
        lfl = f"{fmt(sr[0] * 100, 0)}% vs {fmt(sr[1] * 100, 0)}% ({sr[2]} checks)" if sr else "-"
        print(
            f"| {e['date']} | {fmt(m['content'])} | {fmt(m['structure'])} | {fmt(m['overall'])} | "
            f"{fmt(rates['overall'] * 100, 0)}% | {lfl} | {rates['assessed']} | {c.get('not_checked', 0)} | "
            f"{c.get('fail', 0)} | {c.get('partial', 0)} |"
        )
        prev = e
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="site profile: a folder under profiles/ (fde, eval)")
    ap.add_argument("--catalog", help="checks catalogue (default: the profile's data/checks.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="start a history from the profile's bundled baseline")
    s.add_argument("--history", required=True)
    s.add_argument("--baseline", help="default: the profile's baseline file")
    s.set_defaults(func=cmd_seed)

    n = sub.add_parser("new", help="start a new scores.json from the latest audit")
    n.add_argument("--history", required=True)
    n.add_argument("--date", required=True, help="YYYY-MM-DD of this audit")
    n.add_argument("--out", required=True, help="e.g. .website_spec/site-audits/2026-11-20/scores.json")
    n.add_argument("--site", help="site URL if it changed")
    n.add_argument("--auditor", default="Claude")
    n.add_argument("--start", help="first-audit defaults (site, targets); default: the profile's start file")
    n.add_argument("--replace", action="store_true", help="overwrite an existing file or reuse a date")
    n.set_defaults(func=cmd_new)

    r = sub.add_parser("report", help="score an audit and compare with the previous one")
    r.add_argument("--scores", required=True, help="the new audit's scores.json")
    r.add_argument("--history", required=True)
    r.add_argument("--out", help="write the markdown summary here (default: print)")
    r.add_argument("--append", action="store_true", help="add this audit to the history")
    r.add_argument("--replace", action="store_true", help="with --append: overwrite an audit with the same date")
    r.add_argument("--force", action="store_true", help="show the report despite warnings (never updates history)")
    r.set_defaults(func=cmd_report)

    t = sub.add_parser("trend", help="print every audit in the history")
    t.add_argument("--history", required=True)
    t.set_defaults(func=cmd_trend)

    args = ap.parse_args(argv)
    load_profile(args.profile)
    args.catalog = args.catalog or str(PROFILE["dir"] / "data" / "checks.json")
    if args.cmd == "seed":
        args.baseline = args.baseline or profile_file("baseline")
    if args.cmd == "new":
        args.start = args.start or profile_file("start")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
