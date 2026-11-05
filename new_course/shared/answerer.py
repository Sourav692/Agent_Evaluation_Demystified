"""Answer writers for the RAG half of the refund agent, used from Week 5 on.

Each writer is extractive and deterministic: it answers by quoting sentences from
the retrieved chunks and cites the chunk each sentence came from. That keeps every
result reproducible and free, and it makes faithfulness checkable by string match.

Writer v1 has known bugs on purpose, and Week 5's checks exist to catch them:

1. It quotes any chunk it is given, including superseded and internal ones.
2. It never abstains. When no sentence matches the question, it falls back to a
   stock sentence that appears in no chunk, and cites the first chunk anyway.
3. It ignores conflicts. It picks the best-matching sentences, even when two
   sources disagree, and keeps retrieval order as the tie-breaker.

Writer v2 (Week 6) is added beside v1, never written over it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from shared.retrieval import WORD_TO_CONCEPTS, Chunk, current_public, tokenize

ABSTAIN_TEXT = "I can't find that in our help centre, so I'm passing your question to a specialist."
FALLBACK_V1 = "Refunds are available within 30 days of delivery."
SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Answer:
    text: str
    sentences: list[tuple[str, str | None]] = field(default_factory=list)  # (sentence, cited chunk ID)
    abstained: bool = False
    writer: str = ""

    def citations(self) -> list[str]:
        return [cid for _s, cid in self.sentences if cid]


def split_sentences(chunk: Chunk) -> list[str]:
    """Sentences of a section chunk. The first piece is the heading ("Refund window."), so it is skipped."""
    return SENTENCE.split(chunk.text)[1:]


def _concepts(tokens: list[str]) -> set[str]:
    return {c for t in tokens for c in WORD_TO_CONCEPTS.get(t, [])}


def overlap(question: str, sentence: str) -> float:
    """Shared words, plus half a point per shared concept."""
    q, s = tokenize(question), tokenize(sentence)
    return len(set(q) & set(s)) + 0.5 * len(_concepts(q) & _concepts(s))


def answer_v1(question: str, chunks: list[Chunk], max_sentences: int = 2) -> Answer:
    scored = [(overlap(question, s), rank, s, c.chunk_id)
              for rank, c in enumerate(chunks) for s in split_sentences(c)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    picked = [t for t in scored[:max_sentences] if t[0] >= 1.5]
    if not picked:
        # Bug 2: no abstention. A stock sentence, cited to whatever came first.
        first = chunks[0].chunk_id if chunks else None
        return Answer(FALLBACK_V1, [(FALLBACK_V1, first)], writer="v1")
    sentences = [(s, cid) for _score, _rank, s, cid in picked]
    return Answer(" ".join(s for s, _cid in sentences), sentences, writer="v1")


def is_restricted(chunk: Chunk) -> bool:
    return not current_public(chunk)


def answer_v2(question: str, chunks: list[Chunk], max_sentences: int = 2, min_score: float = 2.0) -> Answer:
    """Writer v2 (Week 6). Two changes from v1, both on purpose:

    - It drops superseded and internal chunks before choosing, as a second layer
      behind the retrieval filter.
    - It abstains when no sentence scores at least `min_score`, instead of guessing.
    """
    usable = [c for c in chunks if current_public(c)]
    scored = [(overlap(question, s), rank, s, c.chunk_id)
              for rank, c in enumerate(usable) for s in split_sentences(c)]
    scored.sort(key=lambda t: (-t[0], t[1]))
    picked = [t for t in scored[:max_sentences] if t[0] >= min_score]
    if not picked:
        return Answer(ABSTAIN_TEXT, [], abstained=True, writer="v2")
    sentences = [(s, cid) for _score, _rank, s, cid in picked]
    return Answer(" ".join(s for s, _cid in sentences), sentences, writer="v2")
