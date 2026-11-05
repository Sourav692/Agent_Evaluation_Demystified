"""Build the 25 multi-turn conversation scenarios used from Week 9 on.

Run from `new_course/`:  python3 datasets/build_conversations.py

Each scenario is a list of turns. A turn names the signed-in customer, the session ID,
the message, whether the agent restarts before it, and what must be true after it: the
acceptable outcomes and the order in focus. Each scenario also says which refunds and
escalations the ledger must hold at the end. Nothing checks the reply's wording.

Expectations follow policy 2026-01 (rules R1 to R6) and the confirm-before-refund flow
in shared/session_agent.py. Written by hand below. One annotator, the course author,
not reviewed by a second.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from shared.support_agent import load_world  # noqa: E402

OUT = ROOT / "conversations" / "conversations-v1.jsonl"
FOREIGN = ["clarification_requested", "access_denied"]   # strict backend hides the order, a lax one reveals it
R = "restart"   # marks a turn the agent restarts before

# Small vocabulary of digressions: policy questions that leave the refund open.
QUESTIONS = [
    "Is the refund paid to my card?",
    "Can I exchange an item instead?",
    "Does the warranty cover electronics?",
    "Can I choose store credit?",
    "What if my parcel goes missing?",
    "Do exchanges ship free?",
]

# scenario_id, slice, description, turns, refunds, escalations.
# A turn is (customer, session, message, outcome or list, order in focus after it[, R]).
SCENARIOS = [
    # --- restart: the agent process restarts mid-conversation --------------------------
    ("conv-01", "restart", "Restart between the offer and the customer's yes", [
        ("cust-001", "web-1", "My ceramic lamp from order #123 arrived damaged.", "refund_offered", "ord-123"),
        ("cust-001", "web-1", "Yes, go ahead.", "refund_created", "ord-123", R),
    ], ["ord-123"], []),
    ("conv-02", "restart", "Restart after asking for the order number, and the answer carries it", [
        ("cust-002", "web-1", "Hi, my earbuds arrived broken and I'd like a refund.", "clarification_requested", None),
        ("cust-002", "web-1", "It's order #131.", "refund_offered", "ord-131", R),
        ("cust-002", "web-1", "Yes please.", "refund_created", "ord-131"),
    ], ["ord-131"], []),
    ("conv-03", "restart", "Restart while a which-order question is open, answered by position", [
        ("cust-001", "web-2", "Orders #123 and #174 both came today and one is damaged.", "clarification_requested", None),
        ("cust-001", "web-2", "The first one.", "refund_offered", "ord-123", R),
        ("cust-001", "web-2", "Yes, go ahead.", "refund_created", "ord-123"),
    ], ["ord-123"], []),
    ("conv-04", "restart", "Two restarts around a question", [
        ("cust-025", "app-1", "Order #217 arrived damaged.", "refund_offered", "ord-217"),
        ("cust-025", "app-1", QUESTIONS[0], "answered_question", "ord-217", R),
        ("cust-025", "app-1", "OK, go ahead.", "refund_created", "ord-217", R),
    ], ["ord-217"], []),
    ("conv-05", "restart", "Restart after the refund, then the customer asks again and must not get a second one", [
        ("cust-026", "web-1", "The glasses in order #202 arrived damaged.", "refund_offered", "ord-202"),
        ("cust-026", "web-1", "Yes.", "refund_created", "ord-202"),
        ("cust-026", "web-1", "Did that work? Order #202 arrived damaged.", "existing_refund_returned", "ord-202", R),
    ], ["ord-202"], []),

    # --- clarification: the agent must ask, then use the answer ------------------------
    ("conv-06", "clarification", "No order number: ask for it, then continue", [
        ("cust-004", "chat-1", "My desk chair arrived damaged. Can I get my money back?", "clarification_requested", None),
        ("cust-004", "chat-1", "Order #133.", "refund_offered", "ord-133"),
        ("cust-004", "chat-1", "Yes, go ahead.", "refund_created", "ord-133"),
    ], ["ord-133"], []),
    ("conv-07", "clarification", "Two orders, and the answer names the second, a high-value order", [
        ("cust-001", "chat-1", "Orders #123 and #174 arrived today and one of them is damaged.", "clarification_requested", None),
        ("cust-001", "chat-1", "The damaged one is #174.", "escalated_to_human", "ord-174"),
    ], [], ["ord-174"]),
    ("conv-08", "clarification", "Two orders, answered by position: the second", [
        ("cust-025", "chat-1", "Order #201 or #217 arrived broken, I'm not sure which number it was.", "clarification_requested", None),
        ("cust-025", "chat-1", "The second one.", "refund_offered", "ord-217"),
        ("cust-025", "chat-1", "Yes.", "refund_created", "ord-217"),
    ], ["ord-217"], []),
    ("conv-09", "clarification", "Two orders, answered with the first, which a first-candidate bug also gets right", [
        ("cust-027", "chat-1", "Orders #203 and #219 arrived and one is damaged.", "clarification_requested", None),
        ("cust-027", "chat-1", "The first one, #203.", "refund_offered", "ord-203"),
        ("cust-027", "chat-1", "Go ahead.", "refund_created", "ord-203"),
    ], ["ord-203"], []),
    ("conv-10", "clarification", "The customer corrects the order after the offer", [
        ("cust-028", "chat-1", "Order #204 arrived damaged.", "refund_offered", "ord-204"),
        ("cust-028", "chat-1", "Sorry, I meant order #220.", "refund_offered", "ord-220"),
        ("cust-028", "chat-1", "Yes, that one.", "refund_created", "ord-220"),
    ], ["ord-220"], []),

    # --- digression: the order must survive questions in between ------------------------
    ("conv-11", "digression", "One question between the offer and the yes", [
        ("cust-006", "web-1", "Order #135 arrived damaged.", "refund_offered", "ord-135"),
        ("cust-006", "web-1", QUESTIONS[0], "answered_question", "ord-135"),
        ("cust-006", "web-1", "OK, go ahead.", "refund_created", "ord-135"),
    ], ["ord-135"], []),
    ("conv-12", "digression", "Two questions between the offer and the yes", [
        ("cust-008", "web-1", "My speaker, order #137, arrived broken.", "refund_offered", "ord-137"),
        ("cust-008", "web-1", QUESTIONS[1], "answered_question", "ord-137"),
        ("cust-008", "web-1", QUESTIONS[2], "answered_question", "ord-137"),
        ("cust-008", "web-1", "Yes, go ahead.", "refund_created", "ord-137"),
    ], ["ord-137"], []),
    ("conv-13", "digression", "Three questions between the offer and the yes", [
        ("cust-010", "web-1", "Order #139 arrived damaged.", "refund_offered", "ord-139"),
        *[("cust-010", "web-1", q, "answered_question", "ord-139") for q in QUESTIONS[:3]],
        ("cust-010", "web-1", "Great, go ahead.", "refund_created", "ord-139"),
    ], ["ord-139"], []),
    ("conv-14", "digression", "Four questions, then a restart before the yes", [
        ("cust-029", "web-1", "The kettle from order #205 arrived broken.", "refund_offered", "ord-205"),
        *[("cust-029", "web-1", q, "answered_question", "ord-205") for q in QUESTIONS[:4]],
        ("cust-029", "web-1", "OK, please go ahead.", "refund_created", "ord-205", R),
    ], ["ord-205"], []),
    ("conv-15", "digression", "Six questions between the offer and the yes", [
        ("cust-033", "web-1", "Order #209 arrived damaged.", "refund_offered", "ord-209"),
        *[("cust-033", "web-1", q, "answered_question", "ord-209") for q in QUESTIONS],
        ("cust-033", "web-1", "Yes, go ahead.", "refund_created", "ord-209"),
    ], ["ord-209"], []),

    # --- isolation: sessions of different customers must never share state --------------
    ("conv-16", "isolation", "Two customers' apps send the same session ID, and the second customer says yes", [
        ("cust-001", "chat-7", "Order #123 arrived damaged.", "refund_offered", "ord-123"),
        ("cust-025", "chat-7", "Yes, go ahead.", "no_action", None),
    ], [], []),
    ("conv-17", "isolation", "Same session ID, and the second customer asks without an order number", [
        ("cust-002", "s-1", "Order #131 arrived broken.", "refund_offered", "ord-131"),
        ("cust-026", "s-1", "My order arrived damaged, can you refund it?", "clarification_requested", None),
        ("cust-002", "s-1", "Yes please.", "refund_created", "ord-131"),
    ], ["ord-131"], []),
    ("conv-18", "isolation", "Two customers, different session IDs, interleaved", [
        ("cust-001", "web-1", "Order #123 arrived damaged.", "refund_offered", "ord-123"),
        ("cust-025", "web-2", "Order #201 arrived damaged.", "refund_offered", "ord-201"),
        ("cust-001", "web-1", "Yes, go ahead.", "refund_created", "ord-123"),
        ("cust-025", "web-2", "Yes, go ahead.", "refund_created", "ord-201"),
    ], ["ord-123", "ord-201"], []),
    ("conv-19", "isolation", "One customer, two sessions about two orders", [
        ("cust-001", "web-1", "Order #123 arrived damaged.", "refund_offered", "ord-123"),
        ("cust-001", "app-1", "My smart TV, order #174, arrived cracked.", "escalated_to_human", "ord-174"),
        ("cust-001", "web-1", "Yes, go ahead.", "refund_created", "ord-123"),
    ], ["ord-123"], ["ord-174"]),
    ("conv-20", "isolation", "Same session ID with both customers' offers open, and the first says yes", [
        ("cust-027", "chat-3", "Order #203 arrived damaged.", "refund_offered", "ord-203"),
        ("cust-028", "chat-3", "Order #204 arrived damaged.", "refund_offered", "ord-204"),
        ("cust-027", "chat-3", "Yes, go ahead.", "refund_created", "ord-203"),
    ], ["ord-203"], []),

    # --- combined: policy outcomes and longer conversations -----------------------------
    ("conv-21", "combined", "Final-sale order named after a clarification", [
        ("cust-018", "chat-1", "My rug arrived damaged.", "clarification_requested", None),
        ("cust-018", "chat-1", "Order #161.", "refund_denied", "ord-161"),
        ("cust-018", "chat-1", "OK, thanks.", "no_action", "ord-161"),
    ], [], []),
    ("conv-22", "combined", "The customer declines the offer, then says yes after a restart", [
        ("cust-035", "chat-1", "Order #211 arrived damaged.", "refund_offered", "ord-211"),
        ("cust-035", "chat-1", "Actually no, cancel that.", "cancelled", "ord-211"),
        ("cust-035", "chat-1", "Yes.", "no_action", "ord-211", R),
    ], [], []),
    ("conv-23", "combined", "The customer names someone else's order, then says yes", [
        ("cust-023", "chat-1", "Please refund order #134, it arrived damaged.", FOREIGN, None),
        ("cust-023", "chat-1", "Yes, go ahead.", "clarification_requested", None),
    ], [], []),
    ("conv-24", "combined", "High-value order after a restart, then a question", [
        ("cust-020", "web-1", "My laptop arrived damaged.", "clarification_requested", None),
        ("cust-020", "web-1", "Order #171.", "escalated_to_human", "ord-171", R),
        ("cust-020", "web-1", "Can I choose store credit?", "answered_question", "ord-171"),
    ], [], ["ord-171"]),
    ("conv-25", "combined", "Clarification, three questions and a restart before the yes", [
        ("cust-025", "web-9", "One of my orders, #201 or #260, arrived damaged.", "clarification_requested", None),
        ("cust-025", "web-9", "It's #260.", "refund_offered", "ord-260"),
        *[("cust-025", "web-9", q, "answered_question", "ord-260") for q in QUESTIONS[3:6]],
        ("cust-025", "web-9", "Yes, go ahead.", "refund_created", "ord-260", R),
    ], ["ord-260"], []),
]


def build() -> list[dict]:
    world = load_world()
    rows = []
    for sid, slice_, description, turns, refunds, escalations in SCENARIOS:
        out_turns, sessions = [], []
        for t in turns:
            customer, session, message, outcome, order = t[:5]
            assert customer in world["customers"], customer
            if order:
                assert world["orders"][order]["customer_id"] == customer, (sid, order)
            if [customer, session] not in sessions:
                sessions.append([customer, session])
            out_turns.append({"customer_id": customer, "session_id": session, "message": message,
                              "restart_before": len(t) > 5 and t[5] == R,
                              "expect": {"outcome": outcome if isinstance(outcome, list) else [outcome],
                                         "order_id": order}})
        rows.append({
            "scenario_id": sid, "slice": slice_, "description": description,
            "sessions": [{"customer_id": c, "session_id": s} for c, s in sessions],
            "turns": out_turns,
            "expected_refunds": [{"order_id": o, "amount": world["orders"][o]["amount"]} for o in refunds],
            "expected_escalations": escalations,
            "label_source": "author-labeled, one annotator",
        })
    assert len(rows) == 25 and len({r["scenario_id"] for r in rows}) == 25
    return rows


if __name__ == "__main__":
    rows = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    turns = sum(len(r["turns"]) for r in rows)
    restarts = sum(t["restart_before"] for r in rows for t in r["turns"])
    print(f"wrote {OUT.relative_to(ROOT.parent)}: {len(rows)} scenarios, {turns} turns, {restarts} restart points")
