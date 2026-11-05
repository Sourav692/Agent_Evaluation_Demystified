"""The help-centre corpus and three local retrievers, used from Week 4 on.

Everything here is deterministic and runs offline:

- `bm25`: keyword retrieval. Scores shared words, weighted by how rare they are.
- `concept`: a small hand-built concept vector. Words map to concepts ("broken",
  "cracked" and "damaged" all count as DAMAGE), so paraphrases can match.
  It stands in for a learned embedding model, which needs a download or a paid API.
  It is not one: it knows only the concepts listed in CONCEPTS.
- `hybrid`: reciprocal rank fusion of the two rankings.

A chunk is relevant to a query when it covers a labeled policy section, so the same
labels work for every chunking strategy.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[1]
DOC_DIRS = (COURSE_ROOT / "datasets" / "policies", COURSE_ROOT / "datasets" / "corpus")

STOPWORDS = set("""a an and are as at be by can do does for from has have how i if in is it its
me my of on or our so that the their them this to was we what when where which who will with
you your""".split())

# Each concept lists the words that count as it. Hand-built for this corpus only.
CONCEPTS = {
    "refund": "refund refunds refunded money back cash reimburse reimbursed repay repaid",
    "damage": "damaged damage broken cracked smashed shattered pieces dented defect defective faulty fault",
    "time_window": "days day window deadline long time within period weeks week late",
    "final_sale": "final sale clearance outlet nonreturnable returnable discounted",
    "approval": "approve approved approval approves review reviewed specialist manager lead escalate",
    "high_value": "expensive pricey over high value large $500 500 $1,000 1,000 $5,000 5,000 $3,000 3,000",
    "ownership": "someone else another owner belongs placed husband wife friend family behalf partner",
    "shipping": "delivery delivered deliver shipping ship shipped courier parcel package dispatch dispatched tracking arrive arrived warehouse leaves",
    "lost": "lost missing stolen vanished",
    "warranty": "warranty guarantee repair repaired fix fixed replace replacement manufacturing",
    "exchange": "exchange exchanged swap size colour color different",
    "credit": "credit voucher store",
    "gift": "gift gifts present recipient",
    "payment": "card payment bank transfer paid pay method account",
    "price": "price cheaper drop drops dropped difference adjustment gap",
    "address": "address move moved change changed",
    "fraud": "fraud suspicious flag flagged",
    "goodwill": "goodwill compensation apology compensate",
    "repeat": "once again twice already repeat second another",
    "order_number": "order number",
}
WORD_TO_CONCEPTS: dict[str, list[str]] = {}
for _concept, _words in CONCEPTS.items():
    for _word in _words.split():
        WORD_TO_CONCEPTS.setdefault(_word, []).append(_concept)

SECTION = re.compile(r"^## ([A-Z]\d+)\. (.+)$", re.MULTILINE)
TOKEN = re.compile(r"\$?\d+(?:[.,]\d+)*%?|[a-z]+\d*")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    status: str            # current or superseded
    audience: str          # public or internal
    section_ids: tuple[str, ...]
    text: str


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower().replace("-", "")) if t not in STOPWORDS]


def _front_matter(raw: str) -> tuple[dict, str]:
    _, head, body = raw.split("---", 2)
    meta = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, body


def load_documents() -> list[dict]:
    """Every policy and help-centre document, with its metadata and sections."""
    docs = []
    for folder in DOC_DIRS:
        for path in sorted(folder.glob("*.md")):
            meta, body = _front_matter(path.read_text())
            parts = SECTION.split(body)
            sections = [{"section_id": f"{meta['doc_id']}#{parts[i]}", "heading": parts[i + 1],
                         "text": parts[i + 2].strip()} for i in range(1, len(parts), 3)]
            docs.append({**meta, "sections": sections})
    return docs


def chunk_documents(docs: list[dict], strategy: str = "section", window: int = 25) -> list[Chunk]:
    """Cut documents into chunks.

    section:  one chunk per numbered section (the default)
    window:   fixed windows of `window` words, ignoring section boundaries
    document: one chunk per document
    """
    chunks = []
    for doc in docs:
        base = dict(doc_id=doc["doc_id"], title=doc["title"], status=doc["status"],
                    audience=doc["audience"])
        if strategy == "section":
            for s in doc["sections"]:
                chunks.append(Chunk(s["section_id"], section_ids=(s["section_id"],),
                                    text=f"{s['heading']}. {s['text']}", **base))
        elif strategy == "document":
            chunks.append(Chunk(doc["doc_id"], section_ids=tuple(s["section_id"] for s in doc["sections"]),
                                text=" ".join(f"{s['heading']}. {s['text']}" for s in doc["sections"]), **base))
        elif strategy == "window":
            words = [(w, s["section_id"]) for s in doc["sections"]
                     for w in f"{s['heading']}. {s['text']}".split()]
            for n, start in enumerate(range(0, len(words), window)):
                piece = words[start:start + window]
                ids = tuple(dict.fromkeys(sid for _w, sid in piece))
                chunks.append(Chunk(f"{doc['doc_id']}@w{n}", section_ids=ids,
                                    text=" ".join(w for w, _sid in piece), **base))
        else:
            raise ValueError(f"unknown chunking strategy: {strategy}")
    return chunks


def current_public(chunk: Chunk) -> bool:
    """The metadata filter for customer-facing answers: current policy, public audience."""
    return chunk.status == "current" and chunk.audience == "public"


class BM25:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.tokens = [tokenize(c.text) for c in chunks]
        self.avg_len = sum(map(len, self.tokens)) / len(self.tokens)
        df = Counter(t for toks in self.tokens for t in set(toks))
        n = len(chunks)
        self.idf = {t: math.log((n - d + 0.5) / (d + 0.5) + 1) for t, d in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for toks in self.tokens:
            tf = Counter(toks)
            norm = self.k1 * (1 - self.b + self.b * len(toks) / self.avg_len)
            out.append(sum(self.idf.get(t, 0) * tf[t] * (self.k1 + 1) / (tf[t] + norm) for t in q if t in tf))
        return out


def concept_vector(text: str, word_weight: float = 0.25) -> Counter:
    """Concept counts, plus raw words at a low weight so exact matches still break ties."""
    vec: Counter = Counter()
    for tok in tokenize(text):
        for concept in WORD_TO_CONCEPTS.get(tok, []):
            vec["concept:" + concept] += 1.0
        vec["word:" + tok] += word_weight
    return vec


def _cosine(a: Counter, b: Counter) -> float:
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class ConceptRetriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectors = [concept_vector(c.text) for c in chunks]

    def scores(self, query: str) -> list[float]:
        q = concept_vector(query)
        return [_cosine(q, v) for v in self.vectors]


def _ranking(scores: list[float]) -> list[int]:
    """Chunk indexes, best first. Ties keep corpus order, so results are reproducible."""
    return sorted(range(len(scores)), key=lambda i: (-scores[i], i))


class Retriever:
    """One interface for all three retrievers: `search(query, k, filtered)`."""

    def __init__(self, chunks: list[Chunk], kind: str = "hybrid", rrf_k: int = 60):
        if kind not in ("bm25", "concept", "hybrid"):
            raise ValueError(f"unknown retriever: {kind}")
        self.chunks, self.kind, self.rrf_k = chunks, kind, rrf_k
        self.bm25, self.concept = BM25(chunks), ConceptRetriever(chunks)

    def ranked(self, query: str) -> list[int]:
        if self.kind == "bm25":
            return _ranking(self.bm25.scores(query))
        if self.kind == "concept":
            return _ranking(self.concept.scores(query))
        fused = [0.0] * len(self.chunks)
        for order in (_ranking(self.bm25.scores(query)), _ranking(self.concept.scores(query))):
            for rank, i in enumerate(order, start=1):
                fused[i] += 1 / (self.rrf_k + rank)
        return _ranking(fused)

    def search(self, query: str, k: int, filtered: bool = True) -> list[Chunk]:
        hits = [self.chunks[i] for i in self.ranked(query)]
        if filtered:
            hits = [c for c in hits if current_public(c)]
        return hits[:k]
