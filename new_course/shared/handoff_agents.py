"""A local multi-agent refund flow, used from Week 10 on: triage hands off to a refund agent
or to a specialist path.

No orchestration framework. A handoff is a plain `Handoff` record passed from one function
to the next. Each agent calls tools through its own `ToolRuntime`, under its own actor name,
and all of them write to one shared refund ledger, so the evaluator can read back what the
whole flow did and which agent did it.

The flow:

- `triage_agent` reads the customer's message. It has no tools. It asks for an order number
  unless the message names exactly one order, routes an explicit request for a person to
  the specialist path, and routes everything else to the refund agent.
- The refund agent checks the order and either refunds it, denies it, or hands an order over
  $500 to the specialist path.
- `specialist_agent` opens a specialist ticket with `escalate_to_specialist`.

Deliberate failure modes:

1. Triage mode `drop_order_id`: the handoff has no order ID, and the summary paraphrases the
   message without the number.
2. Triage mode `drop_identity`: the handoff has no verified customer ID.
3. `Flow(specialist_up=False)`: the specialist path does not accept handoffs.
4. `trusting_refund_agent` trusts whatever it is handed. With no customer ID, it acts as the
   order's owner (a confused deputy). It skips the ownership check because triage "already
   routed it". It hands high-value orders to the specialist path without checking that the
   handoff was accepted, and tells the customer it was.

`refund_agent` is the reference receiver: it rejects a handoff without a customer ID, asks
for a missing order ID, re-checks ownership and eligibility itself, and reports a failed
specialist handoff honestly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from shared.refund_store import RefundStore
from shared.tool_agent import ORDER_ID, AgentResult, order_ids
from shared.tools import ToolRuntime

HANDOFF_FIELDS = ("customer_id", "order_id", "reason")
PERSON_WORDS = re.compile(r"\b(specialist|manager|human|person)\b", re.IGNORECASE)


@dataclass
class Handoff:
    sender: str
    to: str                        # "refund_agent" or "specialist"
    customer_id: str | None        # the verified customer from the signed-in session
    order_id: str | None
    reason: str
    summary: str                   # what the receiver is told about the request


@dataclass
class Flow:
    world: dict
    store: RefundStore
    receiver: object               # the refund agent function: refund_agent or trusting_refund_agent
    strict: bool = True
    specialist_up: bool = True
    handoffs: list[Handoff] = field(default_factory=list)
    runtimes: list[ToolRuntime] = field(default_factory=list)

    def runtime(self, actor: str, customer_id: str | None) -> ToolRuntime:
        rt = ToolRuntime(self.world, customer_id, store=self.store, strict=self.strict, actor=actor)
        self.runtimes.append(rt)
        return rt

    def send(self, handoff: Handoff) -> AgentResult:
        self.handoffs.append(handoff)
        if handoff.to == "specialist":
            return specialist_agent(handoff, self)
        return self.receiver(handoff, self)

    def calls(self) -> list[tuple[str, object]]:
        """Every tool call in the flow, with the actor that made it, in the order the agents ran."""
        return [(rt.actor, call) for rt in self.runtimes for call in rt.trace]


def triage_agent(message: str, customer_id: str, flow: Flow, mode: str = "correct") -> AgentResult:
    ids = order_ids(message)
    if len(ids) != 1:
        ask = "Could you share your order number?" if not ids else "Which order would you like me to look at?"
        return AgentResult(ask, "clarification_requested")
    route = "specialist" if PERSON_WORDS.search(message) else "refund_agent"
    handoff = Handoff("triage", route, customer_id, ids[0],
                      "customer asked for a person" if route == "specialist" else "refund request", message)
    if mode == "drop_order_id":
        handoff.order_id, handoff.summary = None, ORDER_ID.sub("an order", message)
    elif mode == "drop_identity":
        handoff.customer_id = None
    return flow.send(handoff)


def specialist_agent(handoff: Handoff, flow: Flow) -> AgentResult:
    if not flow.specialist_up:
        return AgentResult("", "handoff_not_accepted", handoff.order_id)
    rt = flow.runtime("specialist", handoff.customer_id)
    esc = rt.call("escalate_to_specialist", order_id=handoff.order_id, reason=handoff.reason)
    if esc.error:
        return AgentResult("I couldn't pass this to a specialist. Please try again shortly.",
                           "escalation_failed", handoff.order_id, rt.trace)
    return AgentResult(f"A specialist will review order #{handoff.order_id[4:]}.",
                       "escalated_to_human", handoff.order_id, rt.trace)


def _decide_and_refund(handoff: Handoff, flow: Flow, rt: ToolRuntime, *, check_owner: bool,
                       check_ack: bool) -> AgentResult:
    order_id = handoff.order_id
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return AgentResult(f"I can't find order #{order_id[4:]} on your account.",
                           "clarification_requested", order_id, rt.trace)
    order = got.response
    if check_owner and order["customer_id"] != handoff.customer_id:
        return AgentResult(f"I can't find order #{order_id[4:]} on your account.",
                           "access_denied", order_id, rt.trace)
    if order["refunds"]:
        return AgentResult(f"Order #{order_id[4:]} has already been refunded.",
                           "existing_refund_returned", order_id, rt.trace)
    if order["final_sale"] or order["days_since_delivery"] > 30:
        return AgentResult("That order isn't eligible for a refund.", "refund_denied", order_id, rt.trace)
    if order["amount"] > 500:
        ack = flow.send(Handoff("refund_agent", "specialist", rt.customer_id, order_id,
                                "refund over $500", handoff.summary))
        if check_ack and ack.outcome != "escalated_to_human":
            return AgentResult("I couldn't pass this to a specialist. A person will follow up.",
                               "escalation_failed", order_id, rt.trace)
        return AgentResult(f"Refunds over $500 need a specialist. I've passed order #{order_id[4:]} on.",
                           "escalated_to_human", order_id, rt.trace)
    refund = rt.call("create_refund", order_id=order_id, amount=order["amount"],
                     idempotency_key=f"{rt.customer_id}:{order_id}:refund")
    if refund.error:
        return AgentResult(f"I couldn't issue the refund ({refund.error}).", "refund_failed", order_id, rt.trace)
    return AgentResult(f"I've issued a refund of ${order['amount']:.2f} for order #{order_id[4:]}.",
                       "refund_created", order_id, rt.trace)


def refund_agent(handoff: Handoff, flow: Flow) -> AgentResult:
    """Reference receiver: rejects an incomplete handoff and re-checks everything itself."""
    if handoff.customer_id is None:
        return AgentResult("Something went wrong passing your request on. A person will follow up.",
                           "handoff_rejected", handoff.order_id)
    if handoff.order_id is None:
        return AgentResult("Could you share your order number?", "clarification_requested")
    rt = flow.runtime("refund_agent", handoff.customer_id)
    return _decide_and_refund(handoff, flow, rt, check_owner=True, check_ack=True)


def trusting_refund_agent(handoff: Handoff, flow: Flow) -> AgentResult:
    """Deliberately trusts the handoff. See failure mode 4 in the module docstring."""
    if handoff.order_id is None:
        return AgentResult("Could you share your order number?", "clarification_requested")
    order = flow.world["orders"].get(handoff.order_id)
    acting_as = handoff.customer_id or (order["customer_id"] if order else None)   # the confused deputy
    rt = flow.runtime("refund_agent", acting_as)
    return _decide_and_refund(handoff, flow, rt, check_owner=False, check_ack=False)


RECEIVERS = {"reference": refund_agent, "trusting": trusting_refund_agent}
TRIAGE_MODES = ("correct", "drop_order_id", "drop_identity")


def run_flow(message: str, customer_id: str, world: dict, *, triage_mode: str = "correct",
             receiver: str = "reference", strict: bool = True, specialist_up: bool = True) -> tuple[AgentResult, Flow]:
    flow = Flow(world, RefundStore(world), RECEIVERS[receiver], strict, specialist_up)
    return triage_agent(message, customer_id, flow, triage_mode), flow
