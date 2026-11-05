"""Week 2 lab: validate the versioned refund dataset and its development/holdout split.

Usage, from new_course/:
    python3 weeks/week-02-golden-datasets/handson/lab.py validate              # datasets/manifest.json
    python3 weeks/week-02-golden-datasets/handson/lab.py validate --manifest PATH
    python3 weeks/week-02-golden-datasets/handson/lab.py slices                # agent v1 by slice, development only
    python3 weeks/week-02-golden-datasets/handson/lab.py leak-check FILE       # holdout content in a prompt?

`validate` exits with status 1 when it finds any error, so a script or CI job can stop on it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.support_agent import TOOL_NAMES, load_world, run_agent  # noqa: E402

DATASETS = COURSE / "datasets"
MANIFEST = DATASETS / "manifest.json"

OUTCOMES = {"refund_created", "refund_denied", "escalated_to_human", "access_denied",
            "clarification_requested", "existing_refund_returned"}
SLICES = {"damaged_in_window", "change_of_mind_in_window", "missing_order", "damaged_expired",
          "expired", "final_sale", "high_value", "window_boundary", "amount_boundary",
          "already_refunded", "other_customers_order", "prompt_injection"}
CASE_TYPES = {"positive", "negative", "edge", "adversarial"}
RISKS = {"normal", "high", "critical"}

# field: (allowed Python types, extra rule or None)
SCHEMA = {
    "case_id": ((str,), re.compile(r"^case-\d{4}$")),
    "message": ((str,), None),
    "customer_id": ((str,), re.compile(r"^cust-\d{3}$")),
    "order_id": ((str, type(None)), None),
    "authorized_customer_id": ((str, type(None)), None),
    "policy_version": ((str,), None),
    "slice": ((str,), SLICES),
    "case_type": ((str,), CASE_TYPES),
    "risk": ((str,), RISKS),
    "expected_outcome": ((str,), OUTCOMES),
    "required_keywords": ((list,), None),
    "forbidden_actions": ((list,), None),
    "source": ((str,), None),
}


def known_policy_versions() -> set[str]:
    return {p.stem.removeprefix("refund-policy-") for p in (DATASETS / "policies").glob("refund-policy-*.md")}


# --- One record --------------------------------------------------------------

def validate_record(record: dict, world: dict, policies: set[str]) -> list[str]:
    """Return every problem with one case. An empty list means the record is valid."""
    errors = []
    missing = SCHEMA.keys() - record.keys()
    extra = record.keys() - SCHEMA.keys()
    if missing:
        errors.append(f"missing fields {sorted(missing)}")
    if extra:
        errors.append(f"unknown fields {sorted(extra)}")

    for field, (types, rule) in SCHEMA.items():
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, types):
            errors.append(f"{field} has type {type(value).__name__}")
        elif isinstance(rule, re.Pattern) and not rule.fullmatch(value):
            errors.append(f"{field} {value!r} does not match {rule.pattern}")
        elif isinstance(rule, set) and value not in rule:
            errors.append(f"{field} {value!r} is not one of the allowed values")
    if errors:
        return errors  # the cross-field rules below assume well-formed fields

    if not record["message"].strip():
        errors.append("message is empty")
    if record["policy_version"] not in policies:
        errors.append(f"policy_version {record['policy_version']!r} has no policy file")
    if not record["required_keywords"] or not all(isinstance(k, str) and k for k in record["required_keywords"]):
        errors.append("required_keywords must be a non-empty list of strings")
    unknown_tools = set(record["forbidden_actions"]) - set(TOOL_NAMES)
    if unknown_tools:
        errors.append(f"forbidden_actions names unknown tools {sorted(unknown_tools)}")

    # Label consistency: the label must agree with the world and with itself.
    order = world["orders"].get(record["order_id"]) if record["order_id"] else None
    if record["order_id"] and order is None:
        errors.append(f"order_id {record['order_id']} is not in world.json")
    if order and record["authorized_customer_id"] != order["customer_id"]:
        errors.append(f"authorized_customer_id {record['authorized_customer_id']} "
                      f"but world owner is {order['customer_id']}")
    if (order and record["customer_id"] != order["customer_id"]
            and record["expected_outcome"] != "access_denied"):
        errors.append("requester does not own the order, so expected_outcome must be access_denied")
    if record["expected_outcome"] != "refund_created" and "create_refund" not in record["forbidden_actions"]:
        errors.append("a case that must not refund has to forbid create_refund")
    return errors


# --- A whole dataset ---------------------------------------------------------

def normalize(message: str) -> str:
    """Lower-case and strip punctuation and extra spaces, so trivial edits still match."""
    return " ".join(re.sub(r"[^\w\s]", " ", message.lower()).split())


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    records, errors = [], []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_no}: not valid JSON ({exc.msg})")
            continue
        if not isinstance(record, dict):
            errors.append(f"{path.name}:{line_no}: not a JSON object")
            continue
        record["_line"] = line_no
        records.append(record)
    return records, errors


def validate_dataset(manifest_path: Path = MANIFEST) -> tuple[dict[str, list[dict]], list[str]]:
    """Validate every split named in a manifest. Returns the splits and all errors found."""
    manifest = json.loads(manifest_path.read_text())
    world, policies = load_world(), known_policy_versions()
    splits, errors = {}, []

    if manifest["policy_version"] not in policies:
        errors.append(f"manifest policy_version {manifest['policy_version']!r} has no policy file")

    for name, entry in manifest["splits"].items():
        path = manifest_path.parent / entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            errors.append(f"{name}: file changed since the manifest was written (sha256 mismatch)")
        records, load_errors = load_jsonl(path)
        errors += [f"{name}: {e}" for e in load_errors]
        if len(records) + len(load_errors) != entry["cases"]:
            errors.append(f"{name}: manifest says {entry['cases']} cases, file has "
                          f"{len(records) + len(load_errors)}")
        for record in records:
            line = record.pop("_line")
            where = f"{name}:{line} {record.get('case_id', '?')}"
            errors += [f"{where}: {e}" for e in validate_record(record, world, policies)]
            if record.get("policy_version", manifest["policy_version"]) != manifest["policy_version"]:
                errors.append(f"{where}: policy_version differs from the manifest")
        splits[name] = records

    # Duplicates anywhere, then leakage between splits.
    ids = Counter(r.get("case_id") for records in splits.values() for r in records)
    errors += [f"duplicate case_id {cid} ({n} copies)" for cid, n in sorted(ids.items()) if n > 1]
    if {"development", "holdout"} <= splits.keys():
        errors += split_overlap(splits["development"], splits["holdout"])
    return splits, errors


def split_overlap(development: list[dict], holdout: list[dict]) -> list[str]:
    """Report holdout cases whose ID or normalized message also appears in development."""
    dev_ids = {r.get("case_id") for r in development}
    dev_messages = {normalize(r.get("message", "")): r.get("case_id") for r in development}
    errors = []
    for r in holdout:
        if r.get("case_id") in dev_ids:
            errors.append(f"leakage: {r['case_id']} is in both development and holdout")
        twin = dev_messages.get(normalize(r.get("message", "")))
        if twin and twin != r.get("case_id"):
            errors.append(f"leakage: holdout {r['case_id']} repeats the message of development {twin}")
    return errors


def check_prompt_leakage(text: str, holdout: list[dict]) -> list[str]:
    """Return holdout case IDs whose ID or message appears in a prompt or example file."""
    flat = normalize(text)
    return [r["case_id"] for r in holdout
            if r["case_id"] in text or normalize(r["message"]) in flat]


# --- Slice report --------------------------------------------------------------

def slice_report(cases: list[dict]) -> dict[str, tuple[int, int, int]]:
    """Run agent v1 and count (cases, outcome passes, forbidden calls) per slice."""
    world = load_world()
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for case in cases:
        run = run_agent(case, world)
        row = counts[case["slice"]]
        row[0] += 1
        row[1] += run.outcome == case["expected_outcome"]
        row[2] += any(name in case["forbidden_actions"] for name in run.tool_names())
    return {name: tuple(row) for name, row in counts.items()}


def print_slice_report(cases: list[dict]) -> None:
    report = slice_report(cases)
    risk = {c["slice"]: c["risk"] for c in cases}
    print(f"{'slice':<26} {'risk':<9} {'cases':>5} {'outcome ok':>11} {'forbidden':>10}")
    for name, (n, ok, bad) in sorted(report.items(), key=lambda kv: kv[1][1] / kv[1][0]):
        print(f"{name:<26} {risk[name]:<9} {n:>5} {ok / n:>10.0%} {bad:>10}")
    total = sum(n for n, _ok, _bad in report.values())
    passed = sum(ok for _n, ok, _bad in report.values())
    print(f"{'overall':<26} {'':<9} {total:>5} {passed / total:>10.0%} "
          f"{sum(bad for *_x, bad in report.values()):>10}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="check schema, labels, versions and split leakage")
    v.add_argument("--manifest", type=Path, default=MANIFEST)
    sub.add_parser("slices", help="agent v1 pass rates per slice on the development split")
    leak = sub.add_parser("leak-check", help="look for holdout cases inside a prompt or example file")
    leak.add_argument("file", type=Path)
    args = parser.parse_args()

    if args.command == "validate":
        splits, errors = validate_dataset(args.manifest)
        for name, records in splits.items():
            print(f"{name}: {len(records)} cases")
        for error in errors:
            print(f"ERROR {error}")
        print("valid" if not errors else f"{len(errors)} error(s)")
        sys.exit(1 if errors else 0)

    splits, errors = validate_dataset()
    if errors:
        sys.exit("dataset is invalid; run `validate` first")
    if args.command == "slices":
        print_slice_report(splits["development"])
    else:
        hits = check_prompt_leakage(args.file.read_text(), splits["holdout"])
        print("no holdout content found" if not hits else f"holdout cases found: {hits}")
        sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
