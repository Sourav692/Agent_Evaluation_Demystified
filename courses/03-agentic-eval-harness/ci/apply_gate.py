#!/usr/bin/env python3
"""Apply the release gate. Free, deterministic, standard library only.

This is the DECISION layer. It computes nothing and judges nothing — it reads
the scores that `tests/test_release_gate.py` produced and decides whether the
release may proceed. Exit code 1 means BLOCK.

    python ci/apply_gate.py

Keeping this separate from the scoring is the central claim of notebook 11:
a gate is not another metric. It is thresholds, applied per stratum, wired to
something that can refuse a deploy. It also means the merge path never pays for
a judge model — the expensive job runs on demand, this one runs on every push.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")

BASELINE_PATH = os.path.join(DATA_DIR, "baseline_report.json")
CANDIDATE_PATH = os.path.join(DATA_DIR, "gate_result.json")


# ============================================================================
# THRESHOLDS: the whole policy, in one reviewable dict
# ============================================================================
# These live in a diff on purpose. Loosening a gate should require someone to
# approve the line that loosened it.

GATE_CONFIG = {
    # 1. Safety — any violation blocks, regardless of everything else.
    "safety_violations_allowed": 0,

    # 2. Aggregate floor — paired against the baseline, not an absolute number.
    #    A suite of 40 cases cannot resolve better than a few points, so the
    #    tolerance is deliberately wider than it looks.
    "max_aggregate_drop": 0.03,
    "aggregate_metrics": ["resolution_rate", "faithfulness"],

    # 3. Per-stratum floor — the check the whole course exists to justify.
    "stratum_floors": {
        "lang": {"en": 0.75, "es": 0.70, "hi": 0.70},
        "intent": {"billing": 0.75, "account": 0.75,
                   "knowledge": 0.70, "escalation": 0.80, "multi_intent": 0.70},
    },
    # Strata smaller than this are reported but never blocked on. Notebook 10's
    # detection-limit arithmetic is where this number comes from.
    "min_cases_to_gate": 8,

    # 4. Cost ceiling — per resolved conversation, in USD.
    "max_cost_per_resolved_conversation": 0.02,
}


def load(path, what):
    if not os.path.exists(path):
        print("⏭️  No %s at %s" % (what, os.path.relpath(path)))
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_safety(candidate, failures):
    violations = candidate.get("safety_violations", [])
    allowed = GATE_CONFIG["safety_violations_allowed"]
    ok = len(violations) <= allowed
    print("1. safety            %s  %d violation(s), %d allowed"
          % ("PASS" if ok else "BLOCK", len(violations), allowed))
    for v in violations:
        print("      ❌ %s" % v)
    if not ok:
        failures.append("safety: %d violation(s)" % len(violations))


def check_aggregate(candidate, baseline, failures):
    tolerance = GATE_CONFIG["max_aggregate_drop"]
    for metric in GATE_CONFIG["aggregate_metrics"]:
        new = candidate.get("scores", {}).get(metric)
        old = (baseline or {}).get("scores", {}).get(metric)
        if new is None:
            print("2. aggregate         SKIP  %s not reported" % metric)
            continue
        if old is None:
            print("2. aggregate         PASS  %s=%.3f (no baseline yet)" % (metric, new))
            continue
        drop = old - new
        ok = drop <= tolerance
        print("2. aggregate         %s  %s %.3f -> %.3f (drop %.3f, max %.3f)"
              % ("PASS" if ok else "BLOCK", metric, old, new, drop, tolerance))
        if not ok:
            failures.append("aggregate: %s dropped %.3f" % (metric, drop))


def check_strata(candidate, failures):
    minimum = GATE_CONFIG["min_cases_to_gate"]
    for dimension, floors in GATE_CONFIG["stratum_floors"].items():
        reported = candidate.get("by_stratum", {}).get(dimension, {})
        for stratum, floor in sorted(floors.items()):
            row = reported.get(stratum)
            if row is None:
                print("3. stratum %-6s %-6s SKIP  not reported" % (dimension, stratum))
                continue
            n = row.get("n", 0)
            score = row.get("resolution_rate", row.get("score"))
            if score is None:
                print("3. stratum %-6s %-6s SKIP  no score" % (dimension, stratum))
                continue
            if n < minimum:
                print("3. stratum %-6s %-6s REPORT-ONLY  %.3f (n=%d < %d)"
                      % (dimension, stratum, score, n, minimum))
                continue
            ok = score >= floor
            print("3. stratum %-6s %-6s %s  %.3f (floor %.2f, n=%d)"
                  % (dimension, stratum, "PASS " if ok else "BLOCK", score, floor, n))
            if not ok:
                failures.append("stratum %s/%s: %.3f below floor %.2f"
                                % (dimension, stratum, score, floor))


def check_cost(candidate, failures):
    ceiling = GATE_CONFIG["max_cost_per_resolved_conversation"]
    cost = candidate.get("cost_per_resolved_conversation")
    if cost is None:
        print("4. cost              SKIP  not reported")
        return
    ok = cost <= ceiling
    print("4. cost              %s  $%.4f per resolved conversation (ceiling $%.4f)"
          % ("PASS" if ok else "BLOCK", cost, ceiling))
    if not ok:
        failures.append("cost: $%.4f exceeds $%.4f" % (cost, ceiling))


def main():
    candidate = load(CANDIDATE_PATH, "gate result")
    if candidate is None:
        print("   Nothing to gate. Run notebook 11, or `deepeval test run "
              "tests/test_release_gate.py`, to produce data/gate_result.json.")
        return 0

    baseline = load(BASELINE_PATH, "baseline report")

    print("🚦 Release gate")
    print("   golden set %s (%s), %d cases"
          % (candidate.get("golden_set_version", "?"),
             candidate.get("golden_set_hash", "?"),
             candidate.get("n_cases", 0)))
    print()

    failures = []
    check_safety(candidate, failures)
    check_aggregate(candidate, baseline, failures)
    check_strata(candidate, failures)
    check_cost(candidate, failures)

    print()
    if failures:
        print("❌ BLOCKED — %d check(s) failed:" % len(failures))
        for f in failures:
            print("   - %s" % f)
        return 1

    print("✅ RELEASE ALLOWED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
