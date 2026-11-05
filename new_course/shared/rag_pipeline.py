"""Two versions of the refund agent's RAG pipeline, compared in Week 6.

A version is a fixed configuration: query rewriting, retriever, filter, reranking,
k and answer writer. Both versions run on the same cases, so their results pair up.

Cost and latency here are SIMULATED. Tokens are estimated from word counts, and
latency adds fixed per-step costs to per-token costs. The constants are illustrative
and were not measured on any real system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shared.answerer import Answer, answer_v1, answer_v2, overlap
from shared.retrieval import Chunk, Retriever

# --- Simulated cost and latency (illustrative constants, not measurements) ---------
TOKENS_PER_WORD = 1.3
PRICE_PER_1K_INPUT_TOKENS = 0.0005    # dollars
PRICE_PER_1K_OUTPUT_TOKENS = 0.0015
STEP_MS = {"bm25": 20, "concept": 25, "hybrid": 45, "rewrite": 15, "rerank": 60}
MS_PER_INPUT_TOKEN = 0.2
MS_PER_OUTPUT_TOKEN = 12

# Query rewriting: map customer wording onto the policy's own vocabulary.
REWRITES = {
    "money back": "refund", "cash back": "refund", "send it back": "return refund",
    "changed my mind": "change-of-mind return", "in pieces": "damaged", "broke": "damaged",
    "showed up": "arrived", "turned up": "delivery", "voucher": "store credit",
    "swap": "exchange", "pricey": "high-value over $500",
}


@dataclass(frozen=True)
class PipelineConfig:
    name: str
    retriever: str
    filtered: bool
    rewrite: bool
    rerank: bool
    k: int
    writer: str
    min_score: float = 0.0   # writer v2 abstains when no sentence scores at least this


V1 = PipelineConfig("v1", retriever="bm25", filtered=False, rewrite=False, rerank=False, k=3, writer="v1")
# The candidate. Its abstention threshold was raised to 3.0 to stop guessed answers.
V2 = PipelineConfig("v2", retriever="hybrid", filtered=True, rewrite=True, rerank=True, k=3,
                    writer="v2", min_score=3.0)
# The same candidate with the threshold Week 6's investigation recommends.
V2_1 = PipelineConfig("v2.1", retriever="hybrid", filtered=True, rewrite=True, rerank=True, k=3,
                      writer="v2", min_score=2.0)
VERSIONS = {c.name: c for c in (V1, V2, V2_1)}


def rewrite_query(query: str) -> str:
    """Lower-case, strip punctuation, then swap customer phrases for policy terms.

    Stripping punctuation is meant to make the phrase table match. It also turns
    "$9.99" into "9 99" and "R6?" into "r6", a side effect Week 6 has to find.
    """
    text = re.sub(r"[^\w\s]", " ", query.lower())
    text = " ".join(text.split())
    for phrase, policy_terms in REWRITES.items():
        text = text.replace(phrase, policy_terms)
    return text


def rerank(query: str, chunks: list[Chunk], k: int) -> list[Chunk]:
    """Re-sort the first 10 candidates by their best sentence's overlap with the query.

    A stand-in for a cross-encoder reranker, which reads the query and each chunk together.
    """
    def best(c: Chunk) -> float:
        return max((overlap(query, s) for s in c.text.split(". ")), default=0.0)
    head = sorted(chunks[:10], key=lambda c: -best(c))
    return (head + chunks[10:])[:k]


@dataclass
class PipelineRun:
    query: str
    searched_query: str
    evidence: list[Chunk]
    answer: Answer | None
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float


class Pipeline:
    def __init__(self, config: PipelineConfig, chunks: list[Chunk]):
        self.config = config
        self.retriever = Retriever(chunks, config.retriever)

    def write(self, query: str, evidence: list[Chunk]) -> Answer:
        if self.config.writer == "v1":
            return answer_v1(query, evidence)
        return answer_v2(query, evidence, min_score=self.config.min_score)

    def retrieve(self, query: str) -> tuple[str, list[Chunk]]:
        searched = rewrite_query(query) if self.config.rewrite else query
        depth = 10 if self.config.rerank else self.config.k
        hits = self.retriever.search(searched, depth, filtered=self.config.filtered)
        if self.config.rerank:
            hits = rerank(query, hits, self.config.k)
        return searched, hits[: self.config.k]

    def run(self, query: str, evidence: list[Chunk] | None = None, write: bool = True) -> PipelineRun:
        """Retrieve and answer. Pass `evidence` to skip retrieval (the gold-context swap)."""
        searched, hits = (query, evidence) if evidence is not None else self.retrieve(query)
        answer = self.write(query, hits) if write else None
        words_in = len(query.split()) + sum(len(c.text.split()) for c in hits)
        words_out = len(answer.text.split()) if answer else 0
        tin, tout = round(words_in * TOKENS_PER_WORD), round(words_out * TOKENS_PER_WORD)
        steps = [self.config.retriever] + (["rewrite"] if self.config.rewrite else []) \
            + (["rerank"] if self.config.rerank else [])
        latency = (sum(STEP_MS[s] for s in steps) if evidence is None else 0) \
            + tin * MS_PER_INPUT_TOKEN + tout * MS_PER_OUTPUT_TOKEN
        cost = tin / 1000 * PRICE_PER_1K_INPUT_TOKENS + tout / 1000 * PRICE_PER_1K_OUTPUT_TOKENS
        return PipelineRun(query, searched, hits, answer, tin, tout, cost, latency)
