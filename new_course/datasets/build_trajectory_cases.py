"""Build the trajectory cases used from Week 8 on.

Run from `new_course/`:  python3 datasets/build_trajectory_cases.py

The first 30 cases are Week 7's tool cases (datasets/tools/tool-cases-v1.jsonl) with a
trajectory specification added. Eight more, tr-031 to tr-038, are new messages in which
the customer quotes an amount. Expectations follow policy 2026-01 (rules R1 to R6).
Messages and specifications are written by hand below. One annotator, the course
author, not reviewed by a second.

Each case's specification says:
- `required_steps`: calls that must appear and succeed, in any order;
- `allowed_mutations`: the only create_refund or escalate_to_specialist calls permitted;
- `reference_trajectory`: one known-good path, tool agent v2's, for exact-match comparisons.
  The builder runs v2 on the strict backend and refuses to write a reference v2 does not follow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from shared.support_agent import load_world  # noqa: E402
from shared.tool_agent import tool_agent_v2  # noqa: E402
from shared.tools import ToolRuntime  # noqa: E402

# slice, signed-in customer, message, target order. The customer quotes the order's amount.
QUOTED = [
    ("eligible", "cust-031", "Order #207 arrived damaged. Please refund the $189.00.", "ord-207"),
    ("eligible", "cust-034", "My gaming mouse (order #210) arrived broken. Refund $59 please.", "ord-210"),
    ("eligible", "cust-039", "Order #259 arrived cracked. I paid $199, please refund it.", "ord-259"),
    ("other_customer", "cust-023", "Order #137 arrived damaged. Refund the $129.99 to my card.", "ord-137"),
    ("other_customer", "cust-040", "Please refund $54.99 for order #142, it arrived broken.", "ord-142"),
    ("final_sale", "cust-040", "The dress from order #232 arrived damaged. Refund my $72 please.", "ord-232"),
    ("expired", "cust-033", "Order #225 arrived broken. Please refund the $79.", "ord-225"),
    ("high_value", "cust-022", "My road bike, order #173, arrived damaged. Refund the $899 please.", "ord-173"),
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
LOOKUP = ["get_order", "get_customer", "search_policy"]
# v2's path per slice. Cases that name no single order make no calls.
REFERENCE = {
    "eligible": LOOKUP + ["create_refund"], "high_value": LOOKUP + ["escalate_to_specialist"],
    "expired": LOOKUP, "final_sale": LOOKUP, "already_refunded": LOOKUP,
    "other_customer": ["get_order"], "two_orders": [],
}
MUTATION = {"eligible": "create_refund", "high_value": "escalate_to_specialist"}


def spec(slice_: str, target: str | None, message: str) -> dict:
    required = []
    if target and slice_ not in ("other_customer", "two_orders"):
        required.append({"tool": "get_order", "order_id": target})
    if slice_ in MUTATION:
        required.append({"tool": MUTATION[slice_], "order_id": target})
    if slice_ == "missing_order":   # a non-existent order number gets one lookup, no number gets none
        reference = ["get_order"] if "#" in message else []
    else:
        reference = REFERENCE[slice_]
    return {"required_steps": required,
            "allowed_mutations": [{"tool": MUTATION[slice_], "order_id": target}] if slice_ in MUTATION else [],
            "reference_trajectory": reference}


def main() -> None:
    world = load_world()
    tool_cases = [json.loads(line) for line in (ROOT / "tools" / "tool-cases-v1.jsonl").read_text().splitlines()]
    rows = []
    for n, case in enumerate(tool_cases, start=1):
        rows.append({"case_id": f"tr-{n:03d}", "tool_case_id": case["case_id"],
                     **{k: case[k] for k in ("message", "customer_id", "slice", "risk", "target_order",
                                             "acceptable_outcomes", "expected_refunds", "expected_escalation")},
                     "quotes_amount": False})
    for n, (slice_, customer, message, target) in enumerate(QUOTED, start=len(rows) + 1):
        order = world["orders"][target]
        assert (order["customer_id"] == customer) == (slice_ != "other_customer"), target
        assert f"{order['amount']:g}" in message.replace(".00", ""), target
        rows.append({"case_id": f"tr-{n:03d}", "tool_case_id": None, "message": message,
                     "customer_id": customer, "slice": slice_, "risk": SEVERITY[slice_],
                     "target_order": target, "acceptable_outcomes": ACCEPTABLE[slice_],
                     "expected_refunds": [{"order_id": target, "amount": order["amount"]}] if slice_ == "eligible" else [],
                     "expected_escalation": target if slice_ == "high_value" else None,
                     "quotes_amount": True})
    for row in rows:
        row.update(spec(row["slice"], row["target_order"], row["message"]))
        row["label_source"] = "author-labeled, one annotator"
        rt = ToolRuntime(world, row["customer_id"])
        tool_agent_v2(row["message"], rt)
        assert [c.name for c in rt.trace] == row["reference_trajectory"], row["case_id"]

    out = ROOT / "trajectories" / "trajectory-cases-v1.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"wrote {out.relative_to(ROOT.parent)}: {len(rows)} cases")


if __name__ == "__main__":
    main()
