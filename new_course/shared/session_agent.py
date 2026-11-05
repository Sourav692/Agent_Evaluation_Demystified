"""Multi-turn refund agents with a session checkpoint store. Used from Week 9 on.

A conversation is a series of turns in one session. Each turn the agent receives the
signed-in customer, the session ID and one message, calls tools through a `ToolRuntime`,
and returns a `TurnResult`: the reply, the outcome of the turn and the order it is
working on afterwards. Between turns the agent keeps conversation state: the order in
focus, a pending question, and the candidate orders of an open clarification.

The flow: the customer names an order (or is asked for one), the agent checks it
against policy, offers the refund and waits for a yes before calling create_refund.
Questions in between are answered from the policy search without dropping the order.

Session agent v1 has known bugs on purpose:

1. It keeps every session in a dictionary on the agent object, so a restart loses
   every conversation in progress.
2. It keys sessions by session ID alone, so two customers whose apps send the same
   session ID share one conversation, including each other's order.
3. After asking "which order?", it takes the first candidate whatever the customer
   answers.
4. It rebuilds the order in focus from the orders it looked up in its last 3 turns, so
   a digression of 3 or more turns drops the order.

Session agent v2 is the reference behavior: it checkpoints its state to SQLite after
every turn, keyed by (customer ID, session ID), binds the clarification answer to the
question, and keeps the order as a field of the state rather than re-reading it.

Every reply comes from the REPLIES templates, so a test can reword them all at once.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field

from shared.refund_store import RefundStore
from shared.tool_agent import order_ids
from shared.tools import ToolCall, ToolRuntime

REPLIES = {
    "ask_order": "Could you share your order number?",
    "ask_which": "I can see orders {orders}. Which one is this about?",
    "not_found": "I can't find order #{n} on your account. Could you check the order number?",
    "offer": "Order #{n} ({item}, ${amount:.2f}) can be refunded. Shall I go ahead?",
    "created": "Done. I've refunded ${amount:.2f} for order #{n}.",
    "failed": "I couldn't refund order #{n} ({error}). I've noted it for a specialist.",
    "existing": "Order #{n} has already been refunded ({refund_id}).",
    "final_sale": "Order #{n} was sold as final sale, so it can't be refunded.",
    "expired": "Order #{n} was delivered {days} days ago, outside the 30-day refund window.",
    "escalated": "Refunds over $500 need a specialist. I've passed order #{n} on.",
    "cancelled": "No problem. I won't refund order #{n}.",
    "answer": "{answer}",
    "no_action": "What can I help you with?",
}

CONFIRM = re.compile(r"\b(yes|yeah|yep|go ahead|please do|do it|sure|ok|okay|confirm)\b", re.IGNORECASE)
DECLINE = re.compile(r"\b(no|cancel|don't|do not|never mind|stop)\b", re.IGNORECASE)
REQUEST_WORDS = ("damaged", "broken", "cracked", "money back", "a refund", "refund it", "refund please")
ORDINALS = {"first": 0, "second": 1, "third": 2, "last": -1}
HISTORY_WINDOW = 3          # v1 only: how many recent turns it searches for the order


@dataclass
class TurnResult:
    reply: str
    outcome: str                  # what this turn did, e.g. "refund_offered", "refund_created"
    order_id: str | None          # the order in focus after the turn
    trace: list[ToolCall] = field(default_factory=list)


class SessionStore:
    """Checkpoints: one row of JSON state per (customer, session). A file path survives restarts."""

    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS checkpoints (customer_id TEXT NOT NULL, "
                        "session_id TEXT NOT NULL, state TEXT NOT NULL, PRIMARY KEY (customer_id, session_id))")
        self.db.commit()

    def load(self, customer_id: str, session_id: str) -> dict | None:
        row = self.db.execute("SELECT state FROM checkpoints WHERE customer_id = ? AND session_id = ?",
                              (customer_id, session_id)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, customer_id: str, session_id: str, state: dict) -> None:
        self.db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?)",
                        (customer_id, session_id, json.dumps(state, sort_keys=True)))
        self.db.commit()

    def close(self) -> None:
        self.db.close()


def new_state() -> dict:
    return {"order_id": None, "pending": None, "candidates": [], "turns": 0}


def is_question(message: str) -> bool:
    low = message.lower()
    return "?" in message and not any(w in low for w in REQUEST_WORDS)


def pick_from_answer(candidates: list[str], message: str) -> str | None:
    """Bind the customer's answer to the question asked: an order number, or first/second/last."""
    ids = order_ids(message)
    if len(ids) == 1:
        return ids[0]
    low = message.lower()
    for word, index in ORDINALS.items():
        if re.search(rf"\b{word}\b", low) and -len(candidates) <= index < len(candidates):
            return candidates[index]
    return None


def first_candidate(candidates: list[str], message: str) -> str | None:
    return candidates[0]                                                   # v1 bug 3


def consider(state: dict, order_id: str, rt: ToolRuntime, replies: dict) -> tuple[str, str]:
    """Look the order up and apply policy. Eligible orders get an offer and wait for a yes."""
    got = rt.call("get_order", order_id=order_id)
    n = order_id.removeprefix("ord-")
    if got.error or got.response["customer_id"] != rt.customer_id:
        state.update(order_id=None, pending="order_id")
        outcome = "clarification_requested" if got.error else "access_denied"
        return replies["not_found"].format(n=n), outcome
    order = got.response
    state.update(order_id=order_id, pending=None)
    rt.call("search_policy", query="refund window final sale high value refunds")
    if order["refunds"]:
        return replies["existing"].format(n=n, refund_id=order["refunds"][0]), "existing_refund_returned"
    if order["final_sale"]:
        return replies["final_sale"].format(n=n), "refund_denied"
    if order["days_since_delivery"] > 30:
        return replies["expired"].format(n=n, days=order["days_since_delivery"]), "refund_denied"
    if order["amount"] > 500:
        rt.call("escalate_to_specialist", order_id=order_id, reason="refund over $500")
        return replies["escalated"].format(n=n), "escalated_to_human"
    state["pending"] = "confirm"
    return replies["offer"].format(n=n, item=order["item"], amount=order["amount"]), "refund_offered"


def execute_refund(state: dict, rt: ToolRuntime, replies: dict) -> tuple[str, str]:
    """The customer said yes. Re-read the order, then refund it once, with an idempotency key."""
    order_id = state["order_id"]
    n = order_id.removeprefix("ord-")
    state["pending"] = None
    got = rt.call("get_order", order_id=order_id)
    if got.error:
        return replies["failed"].format(n=n, error=got.error), "refund_failed"
    amount = got.response["amount"]
    made = rt.call("create_refund", order_id=order_id, amount=amount,
                   idempotency_key=f"{rt.customer_id}:{order_id}:refund")
    if made.error:
        return replies["failed"].format(n=n, error=made.error), "refund_failed"
    return replies["created"].format(n=n, amount=amount), "refund_created"


def respond(state: dict, message: str, rt: ToolRuntime, replies: dict, pick) -> tuple[str, str]:
    """One turn of the conversation. Changes `state` in place, returns (reply, outcome)."""
    ids = order_ids(message)
    if state["pending"] == "which_order":
        chosen = pick(state["candidates"], message)
        if chosen is None:
            orders = " and ".join("#" + c.removeprefix("ord-") for c in state["candidates"])
            return replies["ask_which"].format(orders=orders), "clarification_requested"
        state["candidates"] = []
        return consider(state, chosen, rt, replies)
    if len(ids) > 1:
        state.update(order_id=None, pending="which_order", candidates=ids)
        orders = " and ".join("#" + c.removeprefix("ord-") for c in ids)
        return replies["ask_which"].format(orders=orders), "clarification_requested"
    if len(ids) == 1:
        return consider(state, ids[0], rt, replies)
    if state["pending"] == "confirm" and state["order_id"] and DECLINE.search(message):
        state["pending"] = None
        return replies["cancelled"].format(n=state["order_id"].removeprefix("ord-")), "cancelled"
    if CONFIRM.search(message):
        if state["pending"] == "confirm" and state["order_id"]:
            return execute_refund(state, rt, replies)
        if state["pending"] in ("confirm", "order_id"):
            state["pending"] = "order_id"
            return replies["ask_order"], "clarification_requested"
        return replies["no_action"], "no_action"
    if is_question(message):
        hits = rt.call("search_policy", query=message).response or [{"text": ""}]
        sentences = hits[0]["text"].split(". ")
        answer = sentences[1] if len(sentences) > 1 else sentences[0]
        return replies["answer"].format(answer=answer.rstrip(".") + "."), "answered_question"
    if any(w in message.lower() for w in REQUEST_WORDS):
        if state["order_id"]:
            return consider(state, state["order_id"], rt, replies)
        state["pending"] = "order_id"
        return replies["ask_order"], "clarification_requested"
    return replies["no_action"], "no_action"


class SessionAgentV1:
    """Buggy on purpose: see bugs 1 to 4 in the module docstring."""

    def __init__(self, world: dict, ledger: RefundStore, checkpoint_path: str = ":memory:",
                 strict: bool = True, replies: dict = REPLIES):
        self.world, self.ledger, self.strict, self.replies = world, ledger, strict, replies
        self.sessions: dict[str, dict] = {}                                # bugs 1 and 2

    def handle(self, customer_id: str, session_id: str, message: str) -> TurnResult:
        session = self.sessions.setdefault(session_id, {**new_state(), "history": []})
        recent = [h for h in session["history"][-HISTORY_WINDOW:] if h]     # bug 4
        session["order_id"] = recent[-1] if recent else None
        rt = ToolRuntime(self.world, customer_id, store=self.ledger, strict=self.strict)
        reply, outcome = respond(session, message, rt, self.replies, first_candidate)
        looked_up = any(c.name == "get_order" for c in rt.trace)
        session["history"].append(session["order_id"] if looked_up else None)
        session["turns"] += 1
        return TurnResult(reply, outcome, session["order_id"], rt.trace)

    def close(self) -> None:
        pass


class SessionAgentV2:
    """Reference behavior: durable checkpoints keyed by (customer, session)."""

    def __init__(self, world: dict, ledger: RefundStore, checkpoint_path: str = ":memory:",
                 strict: bool = True, replies: dict = REPLIES):
        self.world, self.ledger, self.strict, self.replies = world, ledger, strict, replies
        self.checkpoints = SessionStore(checkpoint_path)

    def handle(self, customer_id: str, session_id: str, message: str) -> TurnResult:
        state = self.checkpoints.load(customer_id, session_id) or new_state()
        rt = ToolRuntime(self.world, customer_id, store=self.ledger, strict=self.strict)
        reply, outcome = respond(state, message, rt, self.replies, pick_from_answer)
        state["turns"] += 1
        self.checkpoints.save(customer_id, session_id, state)   # after the tools ran, before replying
        return TurnResult(reply, outcome, state["order_id"], rt.trace)

    def close(self) -> None:
        self.checkpoints.close()


SESSION_AGENTS = {"v1": SessionAgentV1, "v2": SessionAgentV2}
