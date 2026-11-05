"""The refund agent's tools, as a backend the agent calls. Used from Week 7 on.

Every call goes through `ToolRuntime.call`, which validates nothing about the agent's
intent but records a `ToolCall` with its arguments, its response and any error. That
record is the trace the evaluators read.

Two backend modes:

- `strict=True`: the backend enforces identity, ownership, eligibility and amounts.
  This is how the production backend must behave.
- `strict=False`: the backend trusts the agent. Week 7 uses it to show what the agent
  would have done if nothing stopped it, and that only a read-back of the ledger proves
  what was actually stored.

Faults (Week 10): `faults={"create_refund": ["timeout_after_commit"]}` makes the next
create_refund call commit and then raise a timeout. Each listed fault fires once, in order.
"""

from __future__ import annotations

import copy
import sqlite3
from dataclasses import dataclass, field
from datetime import date

from shared.refund_store import RefundStore
from shared.retrieval import Chunk, Retriever, chunk_documents, load_documents

# Argument schemas: name -> (type, required).
TOOL_SCHEMAS: dict[str, dict[str, tuple[type | tuple[type, ...], bool]]] = {
    "get_customer": {"customer_id": (str, True)},
    "get_order": {"order_id": (str, True)},
    "search_policy": {"query": (str, True)},
    "create_refund": {"order_id": (str, True), "amount": ((int, float), True), "idempotency_key": (str, True)},
    "escalate_to_specialist": {"order_id": (str, True), "reason": (str, True)},
}
MUTATING_TOOLS = {"create_refund", "escalate_to_specialist"}
WINDOW_DAYS, HIGH_VALUE = 30, 500.00


class ToolError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class ToolTimeout(Exception):
    """The caller gave up waiting. The work may or may not have happened."""


@dataclass
class ToolCall:
    name: str
    args: dict
    response: dict | list | None = None
    error: str | None = None      # e.g. "forbidden", "not_eligible", "timeout"


@dataclass
class ToolRuntime:
    world: dict
    customer_id: str                       # the signed-in, verified customer
    store: RefundStore | None = None
    strict: bool = True
    chunks: list[Chunk] | None = None      # Week 10 passes a poisoned corpus here
    faults: dict[str, list[str]] = field(default_factory=dict)
    actor: str = "agent"
    trace: list[ToolCall] = field(default_factory=list)

    def __post_init__(self):
        self.store = self.store or RefundStore(self.world)
        self._retriever = Retriever(self.chunks or chunk_documents(load_documents()), "hybrid")

    # --- the single entry point ---------------------------------------------------------
    def call(self, name: str, **args) -> ToolCall:
        record = ToolCall(name, dict(args))
        self.trace.append(record)
        try:
            handler = getattr(self, f"_tool_{name}", None)
            if handler is None:
                raise ToolError("unknown_tool")
            record.response = handler(**args)
        except ToolError as exc:
            record.error = exc.code
        except ToolTimeout:
            record.error = "timeout"
        except (TypeError, ValueError):
            record.error = "bad_arguments"          # fail closed on malformed arguments
        except sqlite3.IntegrityError:
            record.error = "conflict"               # e.g. an idempotency key already used
        return record

    def _fault(self, name: str) -> str | None:
        queue = self.faults.get(name) or []
        return queue.pop(0) if queue else None

    def _order(self, order_id: str) -> dict:
        order = self.world["orders"].get(order_id)
        if order is None:
            raise ToolError("not_found")
        return order

    # --- tools -----------------------------------------------------------------------------
    def _tool_get_customer(self, customer_id: str) -> dict:
        if self.strict and customer_id != self.customer_id:
            raise ToolError("forbidden")
        customer = self.world["customers"].get(customer_id)
        if customer is None:
            raise ToolError("not_found")
        return dict(customer)

    def _tool_get_order(self, order_id: str) -> dict:
        order = self._order(order_id)
        if self.strict and order["customer_id"] != self.customer_id:
            raise ToolError("not_found")       # never confirm that someone else's order exists
        out = copy.deepcopy(order)
        out["days_since_delivery"] = (self.world["as_of"] - date.fromisoformat(order["delivered_on"])).days
        out["refunds"] = [r["refund_id"] for r in self.store.refunds_for_order(order_id)]
        return out

    def _tool_search_policy(self, query: str) -> list[dict]:
        return [{"chunk_id": c.chunk_id, "text": c.text} for c in self._retriever.search(query, 3)]

    def _tool_create_refund(self, order_id: str, amount, idempotency_key: str | None = None) -> dict:
        order = self._order(order_id)
        if idempotency_key:
            existing = self.store.by_idempotency_key(idempotency_key)
            if existing:
                # A key only replays the caller's own request. In strict mode, a key that
                # belongs to another customer or another order is refused, never replayed.
                if self.strict and (existing["customer_id"] != self.customer_id
                                    or existing["order_id"] != order_id):
                    raise ToolError("forbidden")
                return {**existing, "status": "existing"}
        if self.strict:
            days = (self.world["as_of"] - date.fromisoformat(order["delivered_on"])).days
            if order["customer_id"] != self.customer_id:
                raise ToolError("forbidden")
            if not isinstance(amount, (int, float)) or abs(float(amount) - order["amount"]) > 0.005:
                raise ToolError("invalid_amount")
            if order["final_sale"] or days > WINDOW_DAYS:
                raise ToolError("not_eligible")
            if order["amount"] > HIGH_VALUE:
                raise ToolError("requires_specialist")
            prior = self.store.refunds_for_order(order_id)
            if prior:
                return {**prior[0], "status": "existing"}
        fault = self._fault("create_refund")
        if fault == "timeout_before_commit":
            raise ToolTimeout()
        refund = self.store.insert_refund(order_id, order["customer_id"], float(amount), idempotency_key, self.actor)
        if fault == "timeout_after_commit":
            raise ToolTimeout()
        return {**refund, "status": "created"}

    def _tool_escalate_to_specialist(self, order_id: str, reason: str) -> dict:
        order = self._order(order_id)
        if self.strict and order["customer_id"] != self.customer_id:
            raise ToolError("forbidden")
        self.store.log(self.actor, "escalated", order_id, {"reason": reason})
        return {"ticket_id": f"ticket-{order_id.removeprefix('ord-')}", "status": "escalated"}
