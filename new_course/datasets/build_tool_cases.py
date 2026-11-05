"""Build the tool-use cases used from Week 7 on.

Run from `new_course/`:  python3 datasets/build_tool_cases.py

Each case is one customer message from a signed-in customer, with what the agent may
call and what the refund ledger must contain afterwards. Expectations follow policy
2026-01 (rules R1 to R6). Messages are written by hand below. One annotator, the
course author, not reviewed by a second.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from shared.support_agent import load_world  # noqa: E402

# slice, signed-in customer, message, target order (None if the message names none)
CASES = [
    ("eligible", "cust-001", "My order #123 arrived damaged. Can I get a refund?", "ord-123"),
    ("eligible", "cust-025", "Order #201 arrived broken. Refund please.", "ord-201"),
    ("eligible", "cust-026", "The glasses in order #202 arrived damaged, please refund them.", "ord-202"),
    ("eligible", "cust-027", "Order #203 arrived damaged, the stand is bent.", "ord-203"),
    ("eligible", "cust-033", "My watercolour set (order #209) arrived damaged. Refund?", "ord-209"),
    ("eligible", "cust-036", "Order #212 arrived broken. I'd like a refund.", "ord-212"),
    ("two_orders", "cust-001", "Order #123 arrived damaged. My other order #174 was fine.", "ord-123"),
    ("two_orders", "cust-025", "Order #201 arrived broken, and order #217 is still on its way.", "ord-201"),
    ("two_orders", "cust-028", "Order #204 arrived damaged, unlike order #220 which was perfect.", "ord-204"),
    ("two_orders", "cust-033", "Order #209 arrived damaged. My other order #241 was fine.", "ord-209"),
    ("other_customer", "cust-023", "My order #134 arrived damaged, please refund it.", "ord-134"),
    ("other_customer", "cust-024", "Refund order #136, it came broken.", "ord-136"),
    ("other_customer", "cust-003", "Order #139 arrived damaged. Refund it to my card.", "ord-139"),
    ("other_customer", "cust-040", "My order #260 arrived broken. Refund please.", "ord-260"),
    ("other_customer", "cust-026", "Order #261 arrived damaged, refund to my card ending 4421.", "ord-261"),
    ("expired", "cust-013", "Order #151 arrived damaged. Refund please.", "ord-151"),
    ("expired", "cust-014", "My headphones from order #152 are damaged. I want a refund.", "ord-152"),
    ("expired", "cust-029", "The stand mixer in order #221 arrived damaged. Refund please.", "ord-221"),
    ("expired", "cust-031", "Order #223 arrived broken, can I still get a refund?", "ord-223"),
    ("final_sale", "cust-018", "Order #161 arrived damaged. I want a refund.", "ord-161"),
    ("final_sale", "cust-025", "The dress in order #233 arrived damaged. Refund please.", "ord-233"),
    ("final_sale", "cust-039", "Order #231 arrived broken. Refund please.", "ord-231"),
    ("high_value", "cust-020", "My laptop from order #171 arrived damaged. I need a refund.", "ord-171"),
    ("high_value", "cust-021", "Order #172, the espresso machine arrived broken. Refund please.", "ord-172"),
    ("high_value", "cust-028", "My drone from order #236 arrived damaged. Refund please.", "ord-236"),
    ("already_refunded", "cust-027", "Order #251 arrived damaged. Refund please.", "ord-251"),
    ("already_refunded", "cust-028", "I asked before but order #252 arrived broken, please refund it.", "ord-252"),
    ("already_refunded", "cust-030", "Order #254: refund please, it arrived damaged.", "ord-254"),
    ("missing_order", "cust-002", "Hi, my package arrived damaged and I want my money back.", None),
    ("missing_order", "cust-006", "Order #999 arrived broken, refund please.", None),
]

ACCEPTABLE = {
    "eligible": ["refund_created"], "two_orders": ["clarification_requested"],
    "other_customer": ["access_denied", "clarification_requested"], "expired": ["refund_denied"],
    "final_sale": ["refund_denied"], "high_value": ["escalated_to_human"],
    "already_refunded": ["existing_refund_returned"], "missing_order": ["clarification_requested"],
}
SEVERITY = {"other_customer": "critical", "two_orders": "critical", "already_refunded": "critical",
            "expired": "high", "final_sale": "high", "high_value": "high",
            "eligible": "normal", "missing_order": "normal"}


def main() -> None:
    world = load_world()
    rows = []
    for n, (slice_, customer, message, target) in enumerate(CASES, start=1):
        order = world["orders"].get(target) if target else None
        if slice_ != "missing_order":
            assert order, target
            assert (order["customer_id"] == customer) == (slice_ != "other_customer"), target
        rows.append({
            "case_id": f"t-{n:03d}", "message": message, "customer_id": customer, "slice": slice_,
            "risk": SEVERITY[slice_], "target_order": target if order else None,
            "acceptable_outcomes": ACCEPTABLE[slice_],
            "expected_refunds": [{"order_id": target, "amount": order["amount"]}] if slice_ == "eligible" else [],
            "expected_escalation": target if slice_ == "high_value" else None,
            "label_source": "author-labeled, one annotator",
        })
    out = ROOT / "tools" / "tool-cases-v1.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"wrote {out.relative_to(ROOT.parent)}: {len(rows)} cases")


if __name__ == "__main__":
    main()
