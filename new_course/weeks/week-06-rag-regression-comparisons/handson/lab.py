"""Week 6 lab: compare a baseline and a candidate RAG version on the same cases, and decide.

Usage, from new_course/:
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py scorecard --candidate v2
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py slices --candidate v2
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py paired --candidate v2
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py attribute --version v2
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py decide --candidate v2
    python3 weeks/week-06-rag-regression-comparisons/handson/lab.py ablate --version v2.1

The baseline is always v1. Retrieval is scored with Week 4's metrics on the 50 policy
queries, and answers with Week 5's checks on the 24 answer cases. Cost and latency are
SIMULATED from illustrative constants in shared/rag_pipeline.py, not measured.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.rag_pipeline import VERSIONS, Pipeline  # noqa: E402
from shared.retrieval import chunk_documents, load_documents  # noqa: E402


def load_week_lab(folder: str, name: str):
    """Week 6 reuses Week 4's metrics and Week 5's checks unchanged, so it loads their labs."""
    spec = importlib.util.spec_from_file_location(name, COURSE / "weeks" / folder / "handson" / "lab.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W4 = load_week_lab("week-04-retrieval-evaluation", "week04_lab_for_w6")
W5 = load_week_lab("week-05-answer-quality-and-evidence", "week05_lab_for_w6")
CHUNKS = chunk_documents(load_documents())
BY_ID = {c.chunk_id: c for c in CHUNKS}

# Release policy for this comparison. Illustrative thresholds, to be set from product risk.
POLICY = {
    "max_critical_failures": 0,         # internal text in an answer
    "max_slice_answer_drop": 0,         # passing answer cases lost on any slice
    "max_slice_recall_drop": 0.05,      # Recall@3 lost on any retrieval slice
    "max_p95_latency_increase": 0.20,   # simulated p95 at most 20% above the baseline's
}


# --- Running one version ------------------------------------------------------------

def retrieval_rows(version: str) -> list[dict]:
    pipeline = Pipeline(VERSIONS[version], CHUNKS)
    rows = []
    for q in W4.read_jsonl(W4.QUERIES):
        _searched, hits = pipeline.retrieve(q["query"])
        rows.append({"id": q["query_id"], "slice": q["slice"], **W4.score_query(hits, q["relevance"], 3)})
    return rows


def answer_rows(version: str) -> list[dict]:
    pipeline = Pipeline(VERSIONS[version], CHUNKS)
    rows = []
    for case in W5.read_jsonl(W5.CASES):
        run = pipeline.run(case["question"])
        results = [check(case, run.evidence, run.answer) for check in W5.CHECKS]
        rows.append({"id": case["case_id"], "slice": case["slice"], "case": case, "run": run,
                     "results": results, "passed": all(r.passed for r in results),
                     "critical": any(not r.passed and r.severity == "critical" for r in results)})
    return rows


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile: the smallest value with at least pct% of values at or below it."""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, -(-len(ordered) * pct // 100) - 1))
    return ordered[int(index)]


def summarize(version: str) -> dict:
    ret, ans = retrieval_rows(version), answer_rows(version)
    latencies = [r["run"].latency_ms for r in ans]
    return {
        "version": version, "retrieval": ret, "answers": ans,
        "recall@3": W4.mean(ret, "recall"), "mrr": W4.mean(ret, "mrr"), "ndcg@3": W4.mean(ret, "ndcg"),
        "violations": sum(r["violations"] for r in ret),
        "answers_passed": sum(r["passed"] for r in ans), "critical": sum(r["critical"] for r in ans),
        "abstained": sum(r["run"].answer.abstained for r in ans),
        "cost_per_1k": 1000 * sum(r["run"].cost_usd for r in ans) / len(ans),
        "p50_ms": percentile(latencies, 50), "p95_ms": percentile(latencies, 95),
    }


# --- Comparing two versions -------------------------------------------------------------

def slice_deltas(base: dict, cand: dict) -> list[dict]:
    """Per slice: answer cases passed and retrieval Recall@3, for both versions."""
    out = []
    for kind, rows_key, metric in (("answers", "answers", "passed"), ("retrieval", "retrieval", "recall")):
        groups_b, groups_c = defaultdict(list), defaultdict(list)
        for r in base[rows_key]:
            groups_b[r["slice"]].append(r)
        for r in cand[rows_key]:
            groups_c[r["slice"]].append(r)
        for name in groups_b:
            b = sum(r[metric] for r in groups_b[name])
            c = sum(r[metric] for r in groups_c[name])
            if kind == "retrieval":
                b, c = b / len(groups_b[name]), c / len(groups_c[name])
            out.append({"kind": kind, "slice": name, "n": len(groups_b[name]), "base": b, "cand": c, "delta": c - b})
    return out


def paired(base_rows: list[dict], cand_rows: list[dict], metric: str) -> dict[str, list[str]]:
    """Case by case on the same IDs: which improved, which regressed."""
    cand = {r["id"]: r for r in cand_rows}
    better = [r["id"] for r in base_rows if cand[r["id"]][metric] > r[metric]]
    worse = [r["id"] for r in base_rows if cand[r["id"]][metric] < r[metric]]
    return {"improved": better, "regressed": worse}


def attribute(version: str) -> list[dict]:
    """Gold-context swap: rerun each failing answer case with only its gold sections as evidence.

    Passing with gold evidence means retrieval caused the failure. Failing anyway means generation did.
    """
    pipeline = Pipeline(VERSIONS[version], CHUNKS)
    out = []
    for row in answer_rows(version):
        if row["passed"]:
            continue
        case = row["case"]
        gold = [BY_ID[s] for s in case["gold_sections"]]
        swapped = pipeline.run(case["question"], evidence=gold)
        results = [check(case, gold, swapped.answer) for check in W5.CHECKS]
        cause = "retrieval" if all(r.passed for r in results) else "generation"
        out.append({"id": row["id"], "slice": row["slice"], "cause": cause,
                    "failed": [r.check for r in row["results"] if not r.passed],
                    "failed_with_gold": [r.check for r in results if not r.passed]})
    return out


def ablate(version: str) -> list[dict]:
    """Turn off one component of a version at a time and rerun both evaluations."""
    config = VERSIONS[version]
    variants = [("as configured", config)]
    for field, off in (("rewrite", False), ("rerank", False), ("filtered", False)):
        if getattr(config, field) != off:
            variants.append((f"without {field}", dataclasses.replace(config, name=f"{version}-no-{field}", **{field: off})))
    out = []
    for label, variant in variants:
        VERSIONS[variant.name] = variant
        summary = summarize(variant.name)
        out.append({"label": label, **{k: summary[k] for k in
                    ("ndcg@3", "recall@3", "answers_passed", "critical", "p50_ms")}})
        if variant is not config:
            del VERSIONS[variant.name]
    return out


def decide(base: dict, cand: dict) -> tuple[str, list[str]]:
    """Apply POLICY. Any failed rule blocks the candidate."""
    reasons = []
    if cand["critical"] > POLICY["max_critical_failures"]:
        reasons.append(f"{cand['critical']} critical failures (allowed {POLICY['max_critical_failures']})")
    for d in slice_deltas(base, cand):
        if d["kind"] == "answers" and d["delta"] < -POLICY["max_slice_answer_drop"]:
            reasons.append(f"answer slice '{d['slice']}' drops from {d['base']} to {d['cand']} of {d['n']}")
        if d["kind"] == "retrieval" and d["delta"] < -POLICY["max_slice_recall_drop"]:
            reasons.append(f"retrieval slice '{d['slice']}' Recall@3 drops by {-d['delta']:.3f}")
    budget = base["p95_ms"] * (1 + POLICY["max_p95_latency_increase"])
    if cand["p95_ms"] > budget:
        reasons.append(f"simulated p95 latency {cand['p95_ms']:.0f} ms (budget {budget:.0f} ms)")
    return ("BLOCK" if reasons else "SHIP"), reasons


# --- Printing --------------------------------------------------------------------------

def print_scorecard(base: dict, cand: dict) -> None:
    rows = [("Retrieval Recall@3", "recall@3", "{:.3f}"), ("Retrieval MRR", "mrr", "{:.3f}"),
            ("Retrieval nDCG@3", "ndcg@3", "{:.3f}"), ("Filter violations (150 slots)", "violations", "{:d}"),
            ("Answer cases passing all checks (24)", "answers_passed", "{:d}"),
            ("Critical failures", "critical", "{:d}"), ("Answers abstained", "abstained", "{:d}"),
            ("SIMULATED cost per 1,000 answers ($)", "cost_per_1k", "{:.3f}"),
            ("SIMULATED p50 latency (ms)", "p50_ms", "{:.0f}"), ("SIMULATED p95 latency (ms)", "p95_ms", "{:.0f}")]
    print(f"{'metric':<40}{base['version']:>10}{cand['version']:>10}")
    for label, key, fmt in rows:
        print(f"{label:<40}{fmt.format(base[key]):>10}{fmt.format(cand[key]):>10}")


def print_slices(base: dict, cand: dict) -> None:
    print(f"{'kind':<10}{'slice':<26}{'n':>3}{base['version']:>9}{cand['version']:>9}{'delta':>9}")
    for d in slice_deltas(base, cand):
        fmt = "{:>9.3f}" if d["kind"] == "retrieval" else "{:>9.0f}"
        flag = "  <- regression" if d["delta"] < 0 else ""
        print(f"{d['kind']:<10}{d['slice']:<26}{d['n']:>3}" + fmt.format(d["base"]) + fmt.format(d["cand"])
              + ("{:>+9.3f}" if d["kind"] == "retrieval" else "{:>+9.0f}").format(d["delta"]) + flag)


def print_paired(base: dict, cand: dict) -> None:
    ans = paired(base["answers"], cand["answers"], "passed")
    ret = paired(base["retrieval"], cand["retrieval"], "ndcg")
    print(f"Answer cases ({base['version']} -> {cand['version']}): {len(ans['improved'])} improved, "
          f"{len(ans['regressed'])} regressed")
    print(f"  regressed: {ans['regressed']}")
    print(f"Retrieval queries, nDCG@3: {len(ret['improved'])} improved, {len(ret['regressed'])} regressed")
    print(f"  regressed: {ret['regressed']}")


def print_attribution(version: str) -> None:
    print(f"Gold-context swap for {version}'s failing answer cases:")
    for r in attribute(version):
        print(f"  {r['id']} ({r['slice']}): {r['cause']:<10} failed {r['failed']}, with gold evidence {r['failed_with_gold']}")


def print_decision(base: dict, cand: dict) -> None:
    verdict, reasons = decide(base, cand)
    print(f"Release decision for {cand['version']} against {base['version']}: {verdict}")
    for reason in reasons:
        print(f"  - {reason}")
    print("Thresholds are illustrative (POLICY in lab.py). Latency and cost are simulated.")


def print_ablation(version: str) -> None:
    print(f"Ablation of {version}: one component off at a time")
    print(f"{'variant':<20}{'nDCG@3':>8}{'R@3':>8}{'answers':>9}{'critical':>9}{'p50 ms':>8}")
    for r in ablate(version):
        print(f"{r['label']:<20}{r['ndcg@3']:>8.3f}{r['recall@3']:>8.3f}{r['answers_passed']:>6}/24"
              f"{r['critical']:>9}{r['p50_ms']:>8.0f}")
    print("Latency is simulated.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scorecard", "slices", "paired", "decide"):
        p = sub.add_parser(name)
        p.add_argument("--candidate", default="v2", choices=[v for v in VERSIONS if v != "v1"])
    for name in ("attribute", "ablate"):
        p = sub.add_parser(name)
        p.add_argument("--version", default="v2", choices=list(VERSIONS))
    args = parser.parse_args()
    if args.command in ("attribute", "ablate"):
        (print_attribution if args.command == "attribute" else print_ablation)(args.version)
        return
    base, cand = summarize("v1"), summarize(args.candidate)
    {"scorecard": print_scorecard, "slices": print_slices, "paired": print_paired,
     "decide": print_decision}[args.command](base, cand)


if __name__ == "__main__":
    main()
