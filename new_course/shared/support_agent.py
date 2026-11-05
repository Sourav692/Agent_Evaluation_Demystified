"""A deterministic mock of the customer-support refund agent.

The agent is rule-based so every run gives the same result and costs nothing.
Version v1 is the starting point for Weeks 1-3. It has known bugs on purpose,
and the evaluation labs exist to catch them:

1. It never checks that the order belongs to the signed-in customer.
2. It skips the 30-day window when the message says the item is damaged.
3. It refuses change-of-mind returns that the policy allows.
4. It refunds an order that was already refunded.
5. Its final-sale reply never says "final sale".

Later weeks add new versions instead of editing v1, so earlier labs keep
producing the results their guides describe.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[1]
WORLD_PATH = COURSE_ROOT / "datasets" / "world.json"

AGENT_VERSION = "v1"
TOOL_NAMES = ("get_order", "get_customer", "search_policy", "create_refund")
ORDER_ID_PATTERN = re.compile(r"(?:#|ord-|order\s+(?:number\s+)?)(\d{3,})", re.IGNORECASE)


@dataclass
class ToolCall:
    name: str
    args: dict


@dataclass
class AgentRun:
    """Everything one agent run produced: the trace, the decision and the reply."""

    case_id: str
    agent_version: str
    outcome: str
    final_text: str
    tool_calls: list[ToolCall] = field(default_factory=list)

    def tool_names(self) -> list[str]:
        return [call.name for call in self.tool_calls]

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "agent_version": self.agent_version,
            "outcome": self.outcome,
            "final_text": self.final_text,
            "tool_calls": [{"name": c.name, "args": c.args} for c in self.tool_calls],
        }


def load_world(path: Path = WORLD_PATH) -> dict:
    """Load the synthetic customers and orders, indexed by ID."""
    raw = json.loads(path.read_text())
    return {
        "as_of": date.fromisoformat(raw["as_of"]),
        "customers": {c["customer_id"]: c for c in raw["customers"]},
        "orders": {o["order_id"]: o for o in raw["orders"]},
    }


def parse_order_id(message: str) -> str | None:
    match = ORDER_ID_PATTERN.search(message)
    return f"ord-{match.group(1)}" if match else None


def run_agent(case: dict, world: dict) -> AgentRun:
    """Answer one refund request as agent v1 would.

    `case` needs `case_id`, `customer_id` (the signed-in customer) and `message`.
    """
    run = AgentRun(case["case_id"], AGENT_VERSION, outcome="", final_text="")
    message = case["message"]

    order_id = parse_order_id(message)
    if order_id is None:
        run.outcome = "clarification_requested"
        run.final_text = "I can help with that. Could you share your order number?"
        return run

    run.tool_calls.append(ToolCall("get_order", {"order_id": order_id}))
    order = world["orders"].get(order_id)
    if order is None:
        run.outcome = "clarification_requested"
        run.final_text = (
            f"I couldn't find order #{order_id.removeprefix('ord-')}. "
            "Could you check the order number?"
        )
        return run

    # Bug 1: the agent loads the customer only to greet them by name. It never
    # compares order["customer_id"] with the signed-in customer.
    run.tool_calls.append(ToolCall("get_customer", {"customer_id": case["customer_id"]}))
    customer = world["customers"][case["customer_id"]]
    name = customer["name"].split()[0]
    number = order_id.removeprefix("ord-")

    run.tool_calls.append(ToolCall("search_policy", {"query": "refund policy"}))

    if order["final_sale"]:
        # Bug 5: correct decision, but the reply never names the final-sale rule.
        run.outcome = "refund_denied"
        run.final_text = (
            f"Sorry {name}, the {order['item']} was sold as non-returnable, "
            "so we can't issue a refund for it."
        )
        return run

    if order["amount"] > 500:
        run.outcome = "escalated_to_human"
        run.final_text = (
            f"Thanks {name}. Refunds over $500 need a specialist review, so I've passed "
            f"order #{number} to our refund specialists. They'll contact you within two days."
        )
        return run

    text = message.lower()
    if "damaged" in text or "broken" in text:
        # Bugs 2 and 4: no window check and no check for an existing refund.
        run.tool_calls.append(
            ToolCall("create_refund", {"order_id": order_id, "amount": order["amount"]})
        )
        run.outcome = "refund_created"
        run.final_text = (
            f"I'm sorry the {order['item']} arrived damaged, {name}. I've issued a refund of "
            f"${order['amount']:.2f} for order #{number}. "
            "You'll see it in 3-5 business days."
        )
        return run

    # Bug 3: the policy allows change-of-mind refunds within 30 days.
    run.outcome = "refund_denied"
    run.final_text = (
        f"Sorry {name}, we can only refund items that arrived damaged, "
        f"so order #{number} isn't eligible."
    )
    return run
