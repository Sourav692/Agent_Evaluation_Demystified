"""Week 4 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-04-retrieval-evaluation
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week04_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week04_lab"] = lab
_spec.loader.exec_module(lab)

from shared.retrieval import chunk_documents, current_public, load_documents  # noqa: E402

CHUNKS = {c.chunk_id: c for c in chunk_documents(load_documents())}
HAND = {r["name"][:2]: r for r in lab.read_jsonl(lab.HAND_RANKINGS)}


def scores(name, k):
    row = HAND[name]
    return lab.score_query([CHUNKS[c] for c in row["ranking"]], row["relevance"], k)


def rounded(d):
    return {m: round(d[m], 3) for m in lab.METRICS}


def test_query_set_has_50_labeled_queries_on_current_public_sections():
    queries = lab.read_jsonl(lab.QUERIES)
    assert len(queries) == 50 and len({q["query_id"] for q in queries}) == 50
    assert all(current_public(CHUNKS[s]) for q in queries for s in q["relevance"])


def test_hand_ranking_outdated_first():
    assert rounded(scores("H1", 3)) == {"precision": 0.333, "recall": 1.0, "hit": 1.0, "mrr": 0.5, "ndcg": 0.631}


def test_hand_ranking_answer_at_rank_four():
    assert rounded(scores("H2", 3)) == {"precision": 0.667, "recall": 0.667, "hit": 1.0, "mrr": 1.0, "ndcg": 0.387}
    assert rounded(scores("H2", 5))["ndcg"] == 0.708 and scores("H2", 5)["recall"] == 1.0


def test_best_order_scores_ndcg_one():
    assert scores("H3", 3)["ndcg"] == 1.0


def test_precision_is_capped_by_the_number_of_relevant_sections():
    # One labeled section: even a perfect ranking scores 1/5 at k=5.
    assert scores("H1", 5)["precision"] == 0.2


def test_ndcg_never_exceeds_one_with_window_chunks():
    rows = lab.run_benchmark("hybrid", 5, chunking="window")
    assert max(r["ndcg"] for r in rows) <= 1.0


def test_concept_retriever_beats_bm25_on_paraphrases_and_hybrid_wins_overall_hit_rate():
    bm25, concept, hybrid = (lab.by_slice(lab.run_benchmark(kind, 5)) for kind in ("bm25", "concept", "hybrid"))
    assert lab.mean(bm25["paraphrase"], "recall") == 0.5
    assert round(lab.mean(concept["paraphrase"], "recall"), 3) == 0.85
    assert lab.mean(hybrid["exact_term"], "recall") == 1.0
    assert round(lab.mean(lab.run_benchmark("hybrid", 5), "hit"), 3) == 0.96


def test_metadata_filter_removes_superseded_and_internal_chunks():
    off, on = lab.run_benchmark("hybrid", 5, filtered=False), lab.run_benchmark("hybrid", 5, filtered=True)
    assert sum(r["violations"] for r in off) == 57 and sum(r["violations"] for r in on) == 0
    assert lab.mean(on, "recall") > lab.mean(off, "recall")


def test_document_chunks_buy_recall_with_context_size():
    section, document = lab.run_benchmark("hybrid", 5), lab.run_benchmark("hybrid", 5, chunking="document")
    assert lab.mean(document, "recall") == 1.0
    assert lab.mean(document, "words") > 3 * lab.mean(section, "words")


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-04-retrieval-evaluation-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-04-retrieval-evaluation-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 18


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "ndcg=0.387" in printed
    assert "After:  ['refund-policy-2026-01#R6'" in printed
    assert "Live embeddings" not in printed  # the paid cell is tagged skip-execution


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
