"""Build the answer-evaluation cases used in Weeks 5 and 6.

Run from `new_course/`:  python3 datasets/build_answer_cases.py

Each case fixes the question, the chunks handed to the answer writer, and what a
correct answer must and must not contain. Fixing the retrieved chunks separates
answer quality from retrieval quality: a case fails on the writer alone.

- `normal` cases take the hybrid retriever's filtered top 3, computed here.
- `outdated`, `contradictory`, `missing` and `restricted` cases use retrieved lists
  written by hand to reproduce one evidence problem each.

Labels (must_include, must_not_include, reference_answer, gold_sections) are written
by the course author from the policy text. One annotator, not reviewed by a second.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from shared.retrieval import Retriever, chunk_documents, load_documents  # noqa: E402

RF, OLD, SH, WA, EX, PA, PB = ("refund-policy-2026-01", "refund-policy-2025-06", "shipping-policy-2026-01",
                               "warranty-policy-2026-01", "exchanges-policy-2026-01", "payments-policy-2026-01",
                               "refund-escalation-playbook-2026-01")

# slice, question, retrieved (None = hybrid filtered top 3), behavior, must_include, must_not_include,
# gold sections, reference answer
CASES = [
    ("normal", "How long does a card refund take?", None, "answer", ["3 to 5 business days"], [],
     [f"{PA}#P2"], "Card refunds appear within 3 to 5 business days after they are issued."),
    ("normal", "Does store credit expire?", None, "answer", ["never expires"], [],
     [f"{EX}#E2"], "No. Store credit never expires."),
    ("normal", "How long does standard delivery take?", None, "answer", ["3 to 5 business days"], [],
     [f"{SH}#S1"], "Standard delivery takes 3 to 5 business days."),
    ("normal", "Can I exchange an item for a different size?", None, "answer", ["30 days"], [],
     [f"{EX}#E1"], "Yes, within 30 days of delivery, and the exchange item ships free."),
    ("normal", "What happens if my parcel is lost?", None, "answer", ["10 business days"], [],
     [f"{SH}#S2"], "After 10 business days with no tracking movement the parcel counts as lost, "
                   "and support can send a replacement or a full refund."),
    ("normal", "Can someone else request a refund for my order?", None, "answer",
     ["Only the customer who placed an order"], [], [f"{RF}#R1"],
     "No. Only the customer who placed an order can request a refund for it."),
    ("normal", "Does a warranty claim get me a refund?", None, "answer", ["repair or replacement"], [],
     [f"{WA}#W2"], "Usually not. A valid warranty claim is settled by repair or replacement, "
                   "and a refund is possible only when neither is possible."),
    ("normal", "Who gets the refund for a gift?", None, "answer", ["person who paid"], [],
     [f"{EX}#E3"], "A refund for a gift goes to the person who paid for it."),

    ("outdated", "How long do I have to ask for a refund?", [f"{OLD}#R2", f"{RF}#R2", f"{PA}#P2"], "answer",
     ["30 days"], ["60 days"], [f"{RF}#R2"], "Within 30 days of delivery."),
    ("outdated", "Can anyone with my order number get a refund?", [f"{OLD}#R1", f"{RF}#R1", f"{RF}#R5"], "answer",
     ["Only the customer who placed an order"], ["Any customer with the order number"], [f"{RF}#R1"],
     "No. Only the customer who placed an order can request a refund for it."),
    ("outdated", "Who must approve a big refund?", [f"{OLD}#R4", f"{RF}#R4", f"{RF}#R2"], "answer",
     ["refund specialist"], ["team lead"], [f"{RF}#R4"],
     "A refund over $500 must be reviewed by a refund specialist."),
    ("outdated", "Can final-sale items be refunded if they arrive damaged?", [f"{OLD}#R3", f"{RF}#R3", f"{RF}#R2"],
     "answer", ["cannot be refunded"], ["only when they arrive damaged"], [f"{RF}#R3"],
     "No. Final-sale items cannot be refunded, including when they arrive damaged."),

    ("contradictory", "My item was damaged in transit and I noticed 10 days after delivery. Can I still report it?",
     [f"{SH}#S3", f"{RF}#R2", f"{SH}#S1"], "answer", ["7 days", "30 days"], [], [f"{SH}#S3", f"{RF}#R2"],
     "Transit damage should be reported within 7 days, but reports after that are handled under the refund "
     "policy, which allows a refund request within 30 days of delivery."),
    ("contradictory", "Do I report transit damage within 7 days or 30 days?", [f"{RF}#R2", f"{SH}#S3", f"{PA}#P2"],
     "answer", ["7 days", "30 days"], [], [f"{SH}#S3", f"{RF}#R2"],
     "Report transit damage within 7 days. Later reports fall under the refund policy's 30-day window."),
    ("contradictory", "Can I get a refund instead of a warranty repair for my broken headphones?",
     [f"{WA}#W2", f"{RF}#R2", f"{WA}#W1"], "answer", ["repair or replacement"], [], [f"{WA}#W2", f"{RF}#R2"],
     "Inside the 30-day refund window a refund is possible. After that, a warranty claim is settled by repair "
     "or replacement, and a refund only when neither is possible."),
    ("contradictory", "Do I get store credit or a refund to my card?", [f"{EX}#E2", f"{PA}#P1", f"{RF}#R2"],
     "answer", ["original payment method", "store credit"], [], [f"{EX}#E2", f"{PA}#P1"],
     "Either. A refund goes back to the original payment method, or the customer can choose store credit "
     "worth 110% of the refund."),

    ("missing", "Do you price-match other shops?", [f"{PA}#P3", f"{EX}#E2", f"{SH}#S1"], "abstain", [], [], [],
     "The help centre does not cover price matching. Pass the question to a specialist."),
    ("missing", "Can I pay in monthly instalments?", [f"{PA}#P1", f"{PA}#P2", f"{SH}#S1"], "abstain", [], [], [],
     "The help centre does not cover instalment payments. Pass the question to a specialist."),
    ("missing", "Do you ship to Canada?", [f"{SH}#S1", f"{SH}#S4", f"{SH}#S2"], "abstain", [], [], [],
     "The help centre does not say which countries are served. Pass the question to a specialist."),
    ("missing", "Can I return an item at one of your stores?", [f"{EX}#E1", f"{RF}#R1", f"{RF}#R5"], "abstain",
     [], [], [], "The help centre does not cover in-store returns. Pass the question to a specialist."),

    ("restricted", "Is there compensation for my late parcel?", [f"{PB}#I3", f"{SH}#S1", f"{SH}#S2"], "abstain",
     [], ["goodwill credit", "$25"], [], "The help centre does not offer compensation for late delivery. "
     "Pass the question to a specialist."),
    ("restricted", "Will you flag my account if I want the refund on a new card?", [f"{PB}#I2", f"{PA}#P1", f"{RF}#R6"],
     "answer", ["original payment method"], ["Flag the account", "fraud"], [f"{PA}#P1"],
     "A refund can only go back to the original payment method."),
    ("restricted", "Who approves a $3,000 refund?", [f"{PB}#I1", f"{RF}#R4", f"{RF}#R2"], "answer",
     ["refund specialist"], ["$5,000", "finance manager"], [f"{RF}#R4"],
     "A refund over $500 must be reviewed by a refund specialist."),
    ("restricted", "Can a specialist approve my $800 refund?", [f"{PB}#I1", f"{RF}#R4", f"{PA}#P2"], "answer",
     ["refund specialist"], ["$5,000", "finance manager"], [f"{RF}#R4"],
     "Yes. A refund over $500 is reviewed by a refund specialist."),
]


def main() -> None:
    chunks = chunk_documents(load_documents())
    ids = {c.chunk_id for c in chunks}
    hybrid = Retriever(chunks, "hybrid")
    rows = []
    for n, (slice_, q, retrieved, behavior, must, must_not, gold, ref) in enumerate(CASES, start=1):
        retrieved = retrieved or [c.chunk_id for c in hybrid.search(q, 3)]
        assert set(retrieved) <= ids and set(gold) <= ids, q
        rows.append({"case_id": f"a-{n:03d}", "question": q, "slice": slice_, "retrieved": retrieved,
                     "expected_behavior": behavior, "must_include": must, "must_not_include": must_not,
                     "gold_sections": gold, "reference_answer": ref,
                     "label_source": "author-labeled, one annotator"})
    out = ROOT / "answers" / "answer-cases-v1.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"wrote {out.relative_to(ROOT.parent)}: {len(rows)} cases")


if __name__ == "__main__":
    main()
