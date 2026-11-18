"""Course 04 release gate: ship or don't ship, decided by the rules in gate_rules.json.

Notebook 13 teaches each rule step by step; this file is the same logic in the one place CI can
run it. Standard library only, so the decision can't change because a dependency resolved
differently. Exit codes: 0 ship, 1 a blocking rule failed, 2 an input file is missing.

    python gate.py --baseline data/baseline_scores.json --candidate data/candidate_scores.json \
        --rules gate_rules.json --trust data/judge_trust.json --safety data/safety_scores.json
"""
import argparse
import json
import os
import random
import sys

WRITTEN_BY = {
    "baseline": "notebook 12 (12_statistics_cost_and_experiments.ipynb)",
    "candidate": "notebook 12 (12_statistics_cost_and_experiments.ipynb)",
    "rules": "notebook 13 (13_the_release_gate_and_ci.ipynb)",
    "trust": "notebook 11 (11_calibrating_judges_with_human_labels.ipynb)",
    "safety": "notebook 09 (09_safety_and_red_teaming.ipynb)",
}


def load(path, name, required):
    if not os.path.exists(path):
        message = f"{name}: {path} not found. It is written by {WRITTEN_BY[name]}."
        if required:
            print(f"❌ {message}")
            sys.exit(2)
        print(f"⚠️ {message} Treated as absent.")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slice_rate(cases, metric, slice_name):
    """Pass rate of a boolean metric on one slice; None when no case in the slice has a value."""
    values = [case[metric] for case in cases.values() if case["slice"] == slice_name and case.get(metric) is not None]
    return (sum(values) / len(values), len(values)) if values else (None, 0)


def paired_bootstrap(baseline, candidate, metric, slice_name, resamples, seed, confidence):
    """CI of (candidate − baseline) pass rate on the cases both versions scored, resampling cases."""
    shared = sorted(case_id for case_id, case in candidate.items()
                    if case["slice"] == slice_name and case.get(metric) is not None
                    and baseline.get(case_id, {}).get(metric) is not None)
    if not shared:
        return None
    differences = [int(candidate[c][metric]) - int(baseline[c][metric]) for c in shared]
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(differences) for _ in differences) / len(differences) for _ in range(resamples))
    tail = (1 - confidence) / 2
    low, high = means[int(tail * resamples)], means[int((1 - tail) * resamples) - 1]
    # Round before comparing with 0: float noise such as 1e-18 must not flip a verdict.
    return sum(differences) / len(differences), round(low, 6), round(high, 6), len(shared)


def trusted_metrics(rules, trust):
    trusted = set()
    for row in trust or []:
        if row.get("trusted") and row.get("judge_model") == rules["primary_judge_model"]:
            trusted.add(row["metric"])
    return {metric for metric, judge_metric in rules["judged_metrics"].items() if judge_metric in trusted}


def run_gate(baseline_file, candidate_file, rules, trust, safety):
    """Every rule's result as (rule, status, detail); status is PASS, FAIL, ADVISORY, WARN or SKIP."""
    baseline, candidate = baseline_file["cases"], candidate_file["cases"]
    judged = set(rules["judged_metrics"])
    trusted = trusted_metrics(rules, trust)
    results = []

    def add(rule, ok, detail, metric=None):
        if ok:
            results.append((rule, "PASS", detail))
        elif metric in judged and metric not in trusted:
            results.append((rule, "ADVISORY", detail + " (judge not trusted yet: does not block)"))
        else:
            results.append((rule, "FAIL", detail))

    # 1. Critical safety: counted on the candidate's own runs.
    safety_rules = rules["critical_safety"]
    for metric in safety_rules["metrics"]:
        hits = sorted(c for c, case in candidate.items() if case.get(metric))
        add(f"safety {metric}", len(hits) <= safety_rules["max_count"], f"{len(hits)} found {hits[:5]}")
    known = [row for row in (safety or {}).get("risks", []) if row["critical"] and row["successes"] > 0]
    for row in known:
        detail = f"notebook 09: {row['successes']}/{row['attempts']} {row['risk']} attacks succeeded"
        if safety_rules["block_on_known_safety_findings"]:
            results.append((f"known {row['risk']}", "FAIL", detail))
        else:
            results.append((f"known {row['risk']}", "WARN", detail + " (open finding; set block_on_known_safety_findings to block)"))

    # 2. Slice floors.
    for metric, floors in rules["slice_floors"].items():
        for slice_name, floor in floors.items():
            rate, n = slice_rate(candidate, metric, slice_name)
            if rate is None:
                results.append((f"floor {metric}/{slice_name}", "SKIP", "no scored cases"))
            else:
                add(f"floor {metric}/{slice_name}", rate >= floor, f"{rate:.0%} of {n} (floor {floor:.0%})", metric)

    # 3. No significant regression, per slice.
    settings = rules["regression"]
    slices = sorted({case["slice"] for case in candidate.values()})
    for metric in settings["metrics"]:
        for slice_name in slices:
            result = paired_bootstrap(baseline, candidate, metric, slice_name,
                                      settings["resamples"], settings["seed"], settings["confidence"])
            if result is None:
                continue
            change, low, high, n = result
            add(f"regression {metric}/{slice_name}", high >= 0,
                f"change {change:+.0%}, CI [{low:+.0%}, {high:+.0%}] on {n} paired cases", metric)

    # 4. Budget: mean cost per case.
    costs = [(baseline[c].get("cost_usd"), case.get("cost_usd")) for c, case in candidate.items() if c in baseline]
    costs = [(b, k) for b, k in costs if b is not None and k is not None]
    if not costs or sum(b for b, _ in costs) == 0:
        results.append(("budget cost/case", "SKIP", "no costs recorded"))
    else:
        base_mean = sum(b for b, _ in costs) / len(costs)
        cand_mean = sum(k for _, k in costs) / len(costs)
        limit = base_mean * rules["budget"]["max_cost_ratio"]
        add("budget cost/case", cand_mean <= limit, f"${cand_mean:.5f} vs limit ${limit:.5f} (baseline ${base_mean:.5f})")
    return results


def main():
    parser = argparse.ArgumentParser(description="Course 04 release gate")
    parser.add_argument("--baseline", default="data/baseline_scores.json")
    parser.add_argument("--candidate", default="data/candidate_scores.json")
    parser.add_argument("--rules", default="gate_rules.json")
    parser.add_argument("--trust", default="data/judge_trust.json")
    parser.add_argument("--safety", default="data/safety_scores.json")
    args = parser.parse_args()

    rules = load(args.rules, "rules", required=True)
    baseline = load(args.baseline, "baseline", required=True)
    candidate = load(args.candidate, "candidate", required=True)
    trust = load(args.trust, "trust", required=False)
    safety = load(args.safety, "safety", required=False)
    if candidate.get("synthetic") or baseline.get("synthetic"):
        print("⚠️ Synthetic input: these numbers demonstrate the gate, they are not results.")

    results = run_gate(baseline, candidate, rules, trust, safety)
    for rule, status, detail in results:
        print(f"{status:<9} {rule:<40} {detail}")
    failed = [rule for rule, status, _ in results if status == "FAIL"]
    print(f"\n{'🛑 DO NOT SHIP' if failed else '✅ SHIP'}: {len(failed)} blocking failure(s)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
