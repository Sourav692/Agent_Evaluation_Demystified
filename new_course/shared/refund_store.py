"""The refund ledger: the system of record Weeks 7 to 10 read back, independently of the agent.

SQLite from the standard library. Each run gets its own in-memory database, seeded
with the refunds that already exist in datasets/world.json, so runs never share state.
A file path reopens an existing ledger without seeding it twice.
"""

from __future__ import annotations

import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS refunds (
    refund_id        TEXT PRIMARY KEY,
    order_id         TEXT NOT NULL,
    customer_id      TEXT NOT NULL,
    amount           REAL NOT NULL,
    idempotency_key  TEXT UNIQUE,
    created_by       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    event_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    actor      TEXT NOT NULL,
    action     TEXT NOT NULL,
    order_id   TEXT,
    detail     TEXT NOT NULL
);
"""


class RefundStore:
    def __init__(self, world: dict | None = None, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        already_seeded = self.db.execute("SELECT COUNT(*) FROM refunds").fetchone()[0] > 0
        for order in ([] if already_seeded else (world or {}).get("orders", {}).values()):
            if order.get("existing_refund_id"):
                self.db.execute("INSERT INTO refunds VALUES (?, ?, ?, ?, NULL, 'seed')",
                                (order["existing_refund_id"], order["order_id"], order["customer_id"],
                                 order["amount"]))
        self.db.commit()

    # --- writes ---------------------------------------------------------------------
    def insert_refund(self, order_id: str, customer_id: str, amount: float,
                      idempotency_key: str | None, actor: str) -> dict:
        n = self.db.execute("SELECT COUNT(*) FROM refunds").fetchone()[0] + 1
        refund_id = f"refund-{order_id.removeprefix('ord-')}-{n}"
        self.db.execute("INSERT INTO refunds VALUES (?, ?, ?, ?, ?, ?)",
                        (refund_id, order_id, customer_id, amount, idempotency_key, actor))
        self.log(actor, "refund_created", order_id, {"refund_id": refund_id, "amount": amount})
        self.db.commit()
        return self.refund(refund_id)

    def log(self, actor: str, action: str, order_id: str | None, detail: dict) -> None:
        self.db.execute("INSERT INTO events (actor, action, order_id, detail) VALUES (?, ?, ?, ?)",
                        (actor, action, order_id, json.dumps(detail, sort_keys=True)))
        self.db.commit()

    # --- reads (what the evaluator uses) ---------------------------------------------
    def refund(self, refund_id: str) -> dict | None:
        row = self.db.execute("SELECT * FROM refunds WHERE refund_id = ?", (refund_id,)).fetchone()
        return dict(row) if row else None

    def by_idempotency_key(self, key: str) -> dict | None:
        row = self.db.execute("SELECT * FROM refunds WHERE idempotency_key = ?", (key,)).fetchone()
        return dict(row) if row else None

    def refunds_for_order(self, order_id: str) -> list[dict]:
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM refunds WHERE order_id = ? ORDER BY refund_id", (order_id,))]

    def new_refunds(self) -> list[dict]:
        """Refunds written during this run, excluding the seeded ones."""
        return [dict(r) for r in self.db.execute(
            "SELECT * FROM refunds WHERE created_by != 'seed' ORDER BY rowid")]

    def refunds(self) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM refunds ORDER BY refund_id")]

    def events(self) -> list[dict]:
        return [{**dict(r), "detail": json.loads(r["detail"])}
                for r in self.db.execute("SELECT * FROM events ORDER BY event_id")]
