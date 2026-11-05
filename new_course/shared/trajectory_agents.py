"""Refund-agent variants for trajectory and task-completion evaluation, used from Week 8 on.

Every variant follows tool agent v2 (shared/tool_agent.py) except where listed. Each one
reads one customer message, calls tools through a `ToolRuntime`, and returns an
`AgentResult`. The behaviors below are deliberate, so the checkers have something to find:

- `agent_policy_first`: a valid plan in a different order. It searches the policy before
  looking up the order and never calls get_customer (it greets the customer as "there").
  Every decision and every mutation is the same as v2's.
- `agent_refund_first`: mutates before verifying ownership. When the message quotes an
  amount ("refund the $189"), it calls create_refund with that amount before any
  get_order, then looks the order up only to word the reply. If the backend rejects the
  refund, it falls back to v2's path. Without a quoted amount it behaves exactly like v2.
- `agent_double_checks`: redundant calls. After v2's lookups it calls get_customer and
  search_policy a second time with identical arguments, with no change in between.
- `agent_drops_refund`: does most steps and never stores the refund. It sends the amount
  as text ("64.00") instead of a number, and it claims success without reading what
  create_refund returned. The strict backend rejects the text amount, so nothing is stored.

`AGENTS` maps a short name to each agent, including tool agents v1 and v2.
"""

from __future__ import annotations

import re

from shared.tool_agent import AgentResult, order_ids, tool_agent_v1, tool_agent_v2
from shared.tools import ToolRuntime

AMOUNT = re.compile(r"\$(\d+(?:\.\d{1,2})?)")
POLICY_QUERY = "refund window final sale high value refunds"


def _refund_flow(message: str, rt: ToolRuntime, *, policy_first: bool = False,
                 refund_quoted_first: bool = False, repeat_reads: bool = False,
                 sloppy_refund: bool = False) -> AgentResult:
    """Tool agent v2's path, with one switch per deliberate behavior in the module docstring."""
    ids = order_ids(message)
    if len(ids) != 1:
        ask = "Could you share your order number?" if not ids else "Which order would you like me to look at?"
        return AgentResult(ask, "clarification_requested", trace=rt.trace)
    order_id = ids[0]
    key = f"{rt.customer_id}:{order_id}:refund"
    not_found = f"I can't find order #{order_id[4:]} on your account. Could you check the order number?"

    quoted = AMOUNT.search(message)
    if refund_quoted_first and quoted:                       # mutation before any ownership check
        fast = rt.call("create_refund", order_id=order_id, amount=float(quoted.group(1)), idempotency_key=key)
        if not fast.error:
            rt.call("get_order", order_id=order_id)          # only to word the reply
            return AgentResult(f"I've issued a refund of ${fast.response['amount']:.2f} for order #{order_id[4:]}.",
                               "refund_created", order_id, rt.trace)

    if policy_first:
        rt.call("search_policy", query=POLICY_QUERY)
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return AgentResult(not_found, "clarification_requested", order_id, rt.trace)
    order = got.response
    if order["customer_id"] != rt.customer_id:
        return AgentResult(not_found, "access_denied", order_id, rt.trace)
    name = "there"
    if not policy_first:
        me = rt.call("get_customer", customer_id=rt.customer_id)
        name = me.response["name"].split()[0] if me.response else "there"
        rt.call("search_policy", query=POLICY_QUERY)
    if repeat_reads:                                         # identical reads, nothing changed since
        rt.call("get_customer", customer_id=rt.customer_id)
        rt.call("search_policy", query=POLICY_QUERY)

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

    amount = f"{order['amount']:.2f}" if sloppy_refund else order["amount"]
    refund = rt.call("create_refund", order_id=order_id, amount=amount, idempotency_key=key)
    if not sloppy_refund and (refund.error or refund.response.get("status") not in ("created", "existing")):
        return AgentResult(f"I couldn't issue the refund ({refund.error}). I've noted it for a specialist.",
                           "refund_failed", order_id, rt.trace)
    return AgentResult(f"I've issued a refund of ${order['amount']:.2f} for order #{order_id[4:]}, {name}.",
                       "refund_created", order_id, rt.trace)


def agent_policy_first(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_flow(message, rt, policy_first=True)


def agent_refund_first(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_flow(message, rt, refund_quoted_first=True)


def agent_double_checks(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_flow(message, rt, repeat_reads=True)


def agent_drops_refund(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_flow(message, rt, sloppy_refund=True)


AGENTS = {
    "v1": tool_agent_v1,
    "v2": tool_agent_v2,
    "policy_first": agent_policy_first,
    "refund_first": agent_refund_first,
    "double_checks": agent_double_checks,
    "drops_refund": agent_drops_refund,
}
