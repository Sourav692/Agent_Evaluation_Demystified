"""Release candidates for tool agent v2, used by Week 12's release gate.

Tool agent v2 (shared/tool_agent.py) is the deployed baseline. Each candidate below is a
small, deliberate change to it, written so that one release rule has something to catch:

- v2.1  names the order in every reply. No behavior change. The gate should ship it.
- v2.2  denies refunds over $1,000 instead of escalating them, a misread of policy rule R4.
        One high-value case changes, so the overall average barely moves.
- v2.3  skips its own ownership check when the customer mentions the card a refund should
        go to, as if the card proved ownership. On the strict backend the backend still hides
        other customers' orders, so its release run is identical to v2's. On the lax backend
        it stores one refund on another customer's order.
- v2.4  looks the policy up a second time before deciding. Every check still passes, and
        the extra tool call raises the SIMULATED cost per case.

`refund_agent` is a copy of tool_agent_v2's logic with one switch per change. With every
switch off it behaves exactly like v2, and Week 12's tests check that on all 30 tool cases.
"""

from __future__ import annotations

from shared.tool_agent import AgentResult, order_ids
from shared.tools import ToolRuntime


def refund_agent(message: str, rt: ToolRuntime, *, name_order: bool = False, deny_over: float | None = None,
                 trust_card: bool = False, second_lookup: bool = False) -> AgentResult:
    ids = order_ids(message)
    if len(ids) != 1:
        ask = "Could you share your order number?" if not ids else "Which order would you like me to look at?"
        return AgentResult(ask, "clarification_requested", trace=rt.trace)
    order_id = ids[0]
    ref = f"Order #{order_id[4:]}: " if name_order else ""
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return AgentResult(f"I can't find order #{order_id[4:]} on your account. Could you check the order number?",
                           "clarification_requested", order_id, rt.trace)
    order = got.response
    card_named = "card ending" in message.lower()
    if order["customer_id"] != rt.customer_id and not (trust_card and card_named):   # v2.3 skips this check
        return AgentResult(f"I can't find order #{order_id[4:]} on your account. Could you check the order number?",
                           "access_denied", order_id, rt.trace)
    me = rt.call("get_customer", customer_id=rt.customer_id)
    name = me.response["name"].split()[0] if me.response else "there"
    rt.call("search_policy", query="refund window final sale high value refunds")
    if second_lookup:                                                               # v2.4
        rt.call("search_policy", query="damaged item refund eligibility")
    if order["refunds"]:
        return AgentResult(f"Order #{order_id[4:]} has already been refunded ({order['refunds'][0]}).",
                           "existing_refund_returned", order_id, rt.trace)
    if order["final_sale"]:
        return AgentResult(f"{ref}Sorry {name}, that item was sold as final sale, so it can't be refunded.",
                           "refund_denied", order_id, rt.trace)
    if order["days_since_delivery"] > 30:
        return AgentResult(f"{ref}Sorry {name}, refunds are available within 30 days of delivery.",
                           "refund_denied", order_id, rt.trace)
    if deny_over is not None and order["amount"] > deny_over:                       # v2.2
        return AgentResult(f"{ref}Sorry {name}, we can't refund orders over ${deny_over:,.0f}.",
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


def tool_agent_v2_1(message: str, rt: ToolRuntime) -> AgentResult:
    return refund_agent(message, rt, name_order=True)


def tool_agent_v2_2(message: str, rt: ToolRuntime) -> AgentResult:
    return refund_agent(message, rt, deny_over=1000.0)


def tool_agent_v2_3(message: str, rt: ToolRuntime) -> AgentResult:
    return refund_agent(message, rt, trust_card=True)


def tool_agent_v2_4(message: str, rt: ToolRuntime) -> AgentResult:
    return refund_agent(message, rt, second_lookup=True)


CANDIDATES = {"v2.1": tool_agent_v2_1, "v2.2": tool_agent_v2_2, "v2.3": tool_agent_v2_3, "v2.4": tool_agent_v2_4}
