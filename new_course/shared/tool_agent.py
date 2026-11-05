"""Tool-calling refund agents, used from Week 7 on.

Each agent reads one customer message, calls tools through a `ToolRuntime`, and
returns its reply and the outcome it claims. The runtime keeps the trace, and the
refund ledger keeps what was actually stored. Evaluators read both and never take
the agent's claim on trust.

Tool agent v1 has known bugs on purpose:

1. When a message mentions two orders, it acts on the last one mentioned.
2. It never compares the order's owner with the signed-in customer, and it looks up
   the order's owner with get_customer.
3. It refunds any damaged item without checking the window, final sale, the $500
   limit or an existing refund.
4. It claims success whatever create_refund returned.
5. It sends no idempotency key.

Tool agent v2 is the reference behavior. Later weeks add variants beside these two.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from shared.tools import ToolCall, ToolRuntime

ORDER_ID = re.compile(r"(?:#|ord-|order\s+(?:number\s+)?)(\d{3,})", re.IGNORECASE)
DAMAGE_WORDS = ("damaged", "broken", "cracked")


@dataclass
class AgentResult:
    reply: str
    outcome: str                 # the outcome the agent claims
    order_id: str | None = None
    trace: list[ToolCall] = field(default_factory=list)


def order_ids(message: str) -> list[str]:
    return [f"ord-{n}" for n in ORDER_ID.findall(message)]


def tool_agent_v1(message: str, rt: ToolRuntime) -> AgentResult:
    ids = order_ids(message)
    if not ids:
        return AgentResult("Could you share your order number?", "clarification_requested", trace=rt.trace)
    order_id = ids[-1]                                          # bug 1
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return AgentResult(f"I couldn't find order #{order_id[4:]}. Could you check the order number?",
                           "clarification_requested", order_id, rt.trace)
    order = got.response
    owner = rt.call("get_customer", customer_id=order["customer_id"])   # bug 2
    name = owner.response["name"].split()[0] if owner.response else "there"
    rt.call("search_policy", query="refund policy")
    if any(w in message.lower() for w in DAMAGE_WORDS):
        rt.call("create_refund", order_id=order_id, amount=order["amount"])  # bugs 3 and 5
        return AgentResult(                                                  # bug 4
            f"Sorry about that, {name}. I've issued a refund of ${order['amount']:.2f} for order #{order_id[4:]}.",
            "refund_created", order_id, rt.trace)
    return AgentResult(f"Sorry {name}, we can only refund damaged items.", "refund_denied", order_id, rt.trace)


def tool_agent_v2(message: str, rt: ToolRuntime) -> AgentResult:
    ids = order_ids(message)
    if len(ids) != 1:
        ask = "Could you share your order number?" if not ids else "Which order would you like me to look at?"
        return AgentResult(ask, "clarification_requested", trace=rt.trace)
    order_id = ids[0]
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return AgentResult(f"I can't find order #{order_id[4:]} on your account. Could you check the order number?",
                           "clarification_requested", order_id, rt.trace)
    order = got.response
    if order["customer_id"] != rt.customer_id:      # second layer behind the backend's own check
        return AgentResult(f"I can't find order #{order_id[4:]} on your account. Could you check the order number?",
                           "access_denied", order_id, rt.trace)
    me = rt.call("get_customer", customer_id=rt.customer_id)
    name = me.response["name"].split()[0] if me.response else "there"
    rt.call("search_policy", query="refund window final sale high value refunds")
    if order["refunds"]:
        return AgentResult(f"Order #{order_id[4:]} has already been refunded ({order['refunds'][0]}).",
                           "existing_refund_returned", order_id, rt.trace)
    if order["final_sale"]:
        return AgentResult(f"Sorry {name}, that item was sold as final sale, so it can't be refunded.",
                           "refund_denied", order_id, rt.trace)
    if order["days_since_delivery"] > 30:
        return AgentResult(f"Sorry {name}, refunds are available within 30 days of delivery.",
                           "refund_denied", order_id, rt.trace)
    if order["amount"] > 500:
        esc = rt.call("escalate_to_specialist", order_id=order_id, reason="refund over $500")
        if esc.error:
            return AgentResult("I couldn't pass this to a specialist. Please try again shortly.",
                               "escalation_failed", order_id, rt.trace)
        return AgentResult(f"Refunds over $500 need a specialist, {name}. I've passed order #{order_id[4:]} on.",
                           "escalated_to_human", order_id, rt.trace)
    refund = rt.call("create_refund", order_id=order_id, amount=order["amount"],
                     idempotency_key=f"{rt.customer_id}:{order_id}:refund")
    if refund.error or refund.response.get("status") not in ("created", "existing"):
        return AgentResult(f"I couldn't issue the refund ({refund.error}). I've noted it for a specialist.",
                           "refund_failed", order_id, rt.trace)
    return AgentResult(f"I've issued a refund of ${order['amount']:.2f} for order #{order_id[4:]}, {name}.",
                       "refund_created", order_id, rt.trace)
