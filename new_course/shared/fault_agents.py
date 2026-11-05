"""Refund agents that meet faults, used from Week 10 on.

All five agents make the same decisions as tool agent v2 (shared/tool_agent.py): one order
per message, ownership, an existing refund, final sale, the 30-day window and the $500
limit. They differ in two places only: what they do when `create_refund` times out, and
whether they obey instructions written inside text they read.

Deliberate behaviors:

1. `no_retry_agent` never retries. After a timeout it tells the customer the refund failed.
   When the timeout came after the commit, that claim is false: the ledger holds the refund.
2. `naive_retry_agent` retries a timed-out `create_refund` once, with no idempotency key.
3. `fresh_key_retry_agent` retries once, but makes a new idempotency key for every attempt,
   so the backend cannot tell the retry from a new request.
4. `stable_key_retry_agent` retries once with the same key, `<customer>:<order>:refund`.
   This is the reference behavior.
5. `injectable_agent` retries like the reference, but it obeys any text that contains
   `NOTE TO SUPPORT ASSISTANTS:`, in the customer's message or in a tool response. When it
   finds one, it skips its own ownership and eligibility checks and refunds the order. It
   stands in for a model that follows injected instructions. The marker and every text that
   carries it in this course are synthetic.
"""

from __future__ import annotations

import json

from shared.tool_agent import AgentResult, order_ids
from shared.tools import ToolRuntime

MAX_ATTEMPTS = 2                      # the first call and one retry
POLICY_QUERY = "refund window final sale high value refunds"
INJECTION_MARKER = "note to support assistants:"


def idempotency_key(rt: ToolRuntime, order_id: str, key_mode: str, attempt: int) -> str | None:
    """The key a caller sends with create_refund. `stable` is derived from the request, not the attempt."""
    if key_mode == "none":
        return None
    if key_mode == "fresh":
        return f"{rt.customer_id}:{order_id}:refund:attempt-{attempt}"
    return f"{rt.customer_id}:{order_id}:refund"


def contains_instruction(*texts) -> bool:
    """True when any text, or any tool response serialized to text, carries the injection marker."""
    return any(INJECTION_MARKER in json.dumps(t).lower() for t in texts if t is not None)


def _refund_agent(message: str, rt: ToolRuntime, *, key_mode: str, retry: bool,
                  obeys_instructions: bool) -> AgentResult:
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
    policy = rt.call("search_policy", query=POLICY_QUERY)
    injected = obeys_instructions and contains_instruction(message, policy.response)

    if not injected:                    # tool agent v2's checks, in its order
        if order["customer_id"] != rt.customer_id:
            return AgentResult(f"I can't find order #{order_id[4:]} on your account.",
                               "access_denied", order_id, rt.trace)
        if order["refunds"]:
            return AgentResult(f"Order #{order_id[4:]} has already been refunded ({order['refunds'][0]}).",
                               "existing_refund_returned", order_id, rt.trace)
        if order["final_sale"]:
            return AgentResult("That item was sold as final sale, so it can't be refunded.",
                               "refund_denied", order_id, rt.trace)
        if order["days_since_delivery"] > 30:
            return AgentResult("Refunds are available within 30 days of delivery.",
                               "refund_denied", order_id, rt.trace)
        if order["amount"] > 500:
            esc = rt.call("escalate_to_specialist", order_id=order_id, reason="refund over $500")
            if esc.error:
                return AgentResult("I couldn't pass this to a specialist. Please try again shortly.",
                                   "escalation_failed", order_id, rt.trace)
            return AgentResult(f"Refunds over $500 need a specialist. I've passed order #{order_id[4:]} on.",
                               "escalated_to_human", order_id, rt.trace)

    attempts = MAX_ATTEMPTS if retry else 1
    for attempt in range(1, attempts + 1):
        args = {"order_id": order_id, "amount": order["amount"]}
        key = idempotency_key(rt, order_id, key_mode, attempt)
        if key:
            args["idempotency_key"] = key
        call = rt.call("create_refund", **args)
        if call.error != "timeout":
            break
    if call.error or call.response.get("status") not in ("created", "existing"):
        return AgentResult(f"I couldn't issue the refund ({call.error}). Please try again later.",
                           "refund_failed", order_id, rt.trace)
    return AgentResult(f"I've issued a refund of ${order['amount']:.2f} for order #{order_id[4:]}.",
                       "refund_created", order_id, rt.trace)


def no_retry_agent(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_agent(message, rt, key_mode="stable", retry=False, obeys_instructions=False)


def naive_retry_agent(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_agent(message, rt, key_mode="none", retry=True, obeys_instructions=False)


def fresh_key_retry_agent(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_agent(message, rt, key_mode="fresh", retry=True, obeys_instructions=False)


def stable_key_retry_agent(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_agent(message, rt, key_mode="stable", retry=True, obeys_instructions=False)


def injectable_agent(message: str, rt: ToolRuntime) -> AgentResult:
    return _refund_agent(message, rt, key_mode="stable", retry=True, obeys_instructions=True)


FAULT_AGENTS = {
    "no_retry": no_retry_agent,
    "naive_retry": naive_retry_agent,
    "fresh_key": fresh_key_retry_agent,
    "stable_key": stable_key_retry_agent,
    "injectable": injectable_agent,
}
