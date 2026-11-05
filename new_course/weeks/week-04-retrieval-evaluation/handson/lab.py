"""Week 4 lab: measure retrieval with Precision@k, Recall@k, Hit Rate@k, MRR and nDCG.

Usage, from new_course/:
    python3 weeks/week-04-retrieval-evaluation/handson/lab.py hand            # hand-checkable fixed rankings
    python3 weeks/week-04-retrieval-evaluation/handson/lab.py compare         # retrievers x k, filters, chunking
    python3 weeks/week-04-retrieval-evaluation/handson/lab.py slices --retriever hybrid --k 5
    python3 weeks/week-04-retrieval-evaluation/handson/lab.py query q-009 --retriever concept --k 5
    python3 weeks/week-04-retrieval-evaluation/handson/lab.py dense-live    # PAID: real embeddings

Everything except `dense-live` runs locally on the help-centre corpus in datasets/. No API keys.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.retrieval import Chunk, Retriever, chunk_documents, current_public, load_documents  # noqa: E402

QUERIES = COURSE / "datasets" / "retrieval" / "policy-queries-v1.jsonl"
HAND_RANKINGS = HERE.parent / "dataset" / "hand_rankings.jsonl"
METRICS = ("precision", "recall", "hit", "mrr", "ndcg")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- The five metrics ---------------------------------------------------------
# `ranked` is the retriever's list, best first. `labels` maps a policy section ID to
# its graded relevance: 3 answers the query, 2 is needed context, 1 is related.
# A chunk's grade is the highest grade among the sections it covers.

def chunk_grade(chunk: Chunk, labels: dict[str, int]) -> int:
    return max((labels.get(s, 0) for s in chunk.section_ids), default=0)


def precision_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """Share of the top k chunks that are relevant at all (grade > 0)."""
    return sum(chunk_grade(c, labels) > 0 for c in ranked[:k]) / k


def recall_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """Share of the labeled sections that some top-k chunk covers."""
    covered = {s for c in ranked[:k] for s in c.section_ids if s in labels}
    return len(covered) / len(labels)


def hit_rate_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """1.0 if any top-k chunk is relevant, else 0.0. Averaged over queries it is the hit rate."""
    return 1.0 if any(chunk_grade(c, labels) > 0 for c in ranked[:k]) else 0.0


def reciprocal_rank_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """1 / rank of the first relevant chunk in the top k, or 0. Averaged over queries it is MRR."""
    for rank, c in enumerate(ranked[:k], start=1):
        if chunk_grade(c, labels) > 0:
            return 1 / rank
    return 0.0


def ndcg_at_k(ranked: list[Chunk], labels: dict[str, int], k: int) -> float:
    """Discounted gain of the ranking divided by the gain of the best possible ranking.

    Each labeled section earns its gain once. Without that rule, two window chunks cut
    from the same section would both be credited and nDCG could exceed 1.
    """
    credited: set[str] = set()
    dcg = 0.0
    for rank, c in enumerate(ranked[:k], start=1):
        new = [s for s in c.section_ids if s in labels and s not in credited]
        credited.update(new)
        grade = max((labels[s] for s in new), default=0)
        dcg += (2 ** grade - 1) / math.log2(rank + 1)
    ideal = sorted(labels.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(rank + 1) for rank, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0


def score_query(ranked: list[Chunk], labels: dict[str, int], k: int) -> dict[str, float]:
    return {"precision": precision_at_k(ranked, labels, k), "recall": recall_at_k(ranked, labels, k),
            "hit": hit_rate_at_k(ranked, labels, k), "mrr": reciprocal_rank_at_k(ranked, labels, k),
            "ndcg": ndcg_at_k(ranked, labels, k),
            "violations": sum(not current_public(c) for c in ranked[:k]),
            "words": sum(len(c.text.split()) for c in ranked[:k])}


# --- Benchmark ------------------------------------------------------------------

def run_benchmark(kind: str, k: int, filtered: bool = True, chunking: str = "section",
                  queries: list[dict] | None = None) -> list[dict]:
    """Retrieve for every query and score it. One row per query."""
    queries = queries or read_jsonl(QUERIES)
    retriever = Retriever(chunk_documents(load_documents(), chunking), kind)
    rows = []
    for q in queries:
        ranked = retriever.search(q["query"], k, filtered=filtered)
        rows.append({"query_id": q["query_id"], "slice": q["slice"], **score_query(ranked, q["relevance"], k)})
    return rows


def mean(rows: list[dict], metric: str) -> float:
    return sum(r[metric] for r in rows) / len(rows)


def by_slice(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["slice"]].append(r)
    return dict(groups)


def print_metric_row(label: str, rows: list[dict], extra: str = "") -> None:
    cells = "  ".join(f"{mean(rows, m):>6.3f}" for m in METRICS)
    print(f"{label:<30} {cells}  {sum(r['violations'] for r in rows):>5}  {mean(rows, 'words'):>6.0f}{extra}")


def print_header(first: str) -> None:
    print(f"{first:<30} {'P@k':>6}  {'R@k':>6}  {'Hit':>6}  {'MRR':>6}  {'nDCG':>6}  {'viol':>5}  {'words':>6}")


def print_compare() -> None:
    print("Retrievers, filtered to current public policy, section chunks:")
    print_header("retriever @ k")
    for kind in ("bm25", "concept", "hybrid"):
        for k in (3, 5):
            print_metric_row(f"{kind} @ {k}", run_benchmark(kind, k))

    print("\nMetadata filter, hybrid @ 5:")
    print_header("filter")
    for filtered in (False, True):
        print_metric_row("on" if filtered else "off", run_benchmark("hybrid", 5, filtered=filtered))

    print("\nChunking, hybrid @ 5, filtered:")
    print_header("chunking")
    for chunking in ("section", "window", "document"):
        print_metric_row(chunking, run_benchmark("hybrid", 5, chunking=chunking))


def print_slices(kind: str, k: int) -> None:
    rows = run_benchmark(kind, k)
    print(f"{kind} @ {k} by slice (filtered, section chunks):")
    print_header("slice (queries)")
    for name, group in sorted(by_slice(rows).items(), key=lambda kv: mean(kv[1], "recall")):
        print_metric_row(f"{name} ({len(group)})", group)
    print_metric_row(f"overall ({len(rows)})", rows)


def print_query(query_id: str, kind: str, k: int, filtered: bool) -> None:
    q = next((q for q in read_jsonl(QUERIES) if q["query_id"] == query_id), None)
    if q is None:
        sys.exit(f"unknown query ID: {query_id}")
    retriever = Retriever(chunk_documents(load_documents()), kind)
    ranked = retriever.search(q["query"], k, filtered=filtered)
    print(f"{query_id} ({q['slice']}): {q['query']}")
    print(f"labels: {q['relevance']}")
    for rank, c in enumerate(ranked, start=1):
        flag = "" if current_public(c) else f"  <- {c.status}/{c.audience}"
        print(f"  {rank}. {c.chunk_id:<38} grade {chunk_grade(c, q['relevance'])}{flag}")
    print("  " + "  ".join(f"{m}={v:.3f}" for m, v in score_query(ranked, q["relevance"], k).items()))


def print_hand() -> None:
    """Score the fixed rankings in dataset/hand_rankings.jsonl. Check them by hand first."""
    by_id = {c.chunk_id: c for c in chunk_documents(load_documents())}
    for row in read_jsonl(HAND_RANKINGS):
        ranked = [by_id[cid] for cid in row["ranking"]]
        print(f"{row['name']}: labels {row['relevance']}")
        for k in (3, 5):
            scores = score_query(ranked, row["relevance"], k)
            print(f"  k={k}  " + "  ".join(f"{m}={scores[m]:.3f}" for m in METRICS))


def dense_live(model: str = "text-embedding-3-small", k: int = 5) -> None:
    """Compare a real embedding retriever with BM25 hybrid. Costs money: needs `openai` and OPENAI_API_KEY.

    One embeddings call for the 26 chunks and one for the 50 queries.
    """
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. dense-live is optional; every other command runs offline.")
    from openai import OpenAI  # requirements-integrations.txt

    client = OpenAI()
    chunks = [c for c in chunk_documents(load_documents()) if current_public(c)]
    queries = read_jsonl(QUERIES)

    def embed(texts: list[str]) -> list[list[float]]:
        return [d.embedding for d in client.embeddings.create(model=model, input=texts).data]

    def cos(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

    chunk_vecs, query_vecs = embed([c.text for c in chunks]), embed([q["query"] for q in queries])
    bm25 = Retriever(chunks, "bm25")
    dense_rows, hybrid_rows = [], []
    for q, qv in zip(queries, query_vecs):
        dense_order = sorted(range(len(chunks)), key=lambda i: -cos(qv, chunk_vecs[i]))
        fused = [0.0] * len(chunks)
        for order in (dense_order, bm25.ranked(q["query"])):
            for rank, i in enumerate(order, start=1):
                fused[i] += 1 / (60 + rank)
        hybrid_order = sorted(range(len(chunks)), key=lambda i: (-fused[i], i))
        for rows, order in ((dense_rows, dense_order), (hybrid_rows, hybrid_order)):
            rows.append({"query_id": q["query_id"], "slice": q["slice"],
                         **score_query([chunks[i] for i in order], q["relevance"], k)})
    print(f"Live embeddings ({model}), filtered, k={k}:")
    print_header("retriever")
    print_metric_row("dense", dense_rows)
    print_metric_row("dense + bm25 hybrid", hybrid_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hand", help="metrics for the fixed rankings")
    sub.add_parser("compare", help="retrievers x k, filter on/off, chunking")
    s = sub.add_parser("slices", help="per-slice metrics for one configuration")
    s.add_argument("--retriever", default="hybrid", choices=["bm25", "concept", "hybrid"])
    s.add_argument("--k", type=int, default=5)
    q = sub.add_parser("query", help="one query's ranking and metrics")
    q.add_argument("query_id")
    q.add_argument("--retriever", default="hybrid", choices=["bm25", "concept", "hybrid"])
    q.add_argument("--k", type=int, default=5)
    q.add_argument("--unfiltered", action="store_true")
    d = sub.add_parser("dense-live", help="PAID: real embedding retriever versus hybrid")
    d.add_argument("--model", default="text-embedding-3-small")
    args = parser.parse_args()
    if args.command == "hand":
        print_hand()
    elif args.command == "compare":
        print_compare()
    elif args.command == "slices":
        print_slices(args.retriever, args.k)
    elif args.command == "dense-live":
        dense_live(args.model)
    else:
        print_query(args.query_id, args.retriever, args.k, not args.unfiltered)


if __name__ == "__main__":
    main()
