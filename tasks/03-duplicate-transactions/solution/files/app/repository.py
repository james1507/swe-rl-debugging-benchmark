"""SQLite-enforced idempotency, including retries from separate processes."""
from contextlib import closing
from pathlib import Path
import sqlite3


class TransactionRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        # ponytail: fresh databases only; add a migration for legacy duplicate rows.
        with closing(sqlite3.connect(self.db_path, timeout=15)) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transfers (
                    id INTEGER PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    amount_cents INTEGER NOT NULL
                        CHECK(typeof(amount_cents) = 'integer' AND amount_cents > 0)
                )
            """)

    def transfer(self, request_id: str, amount_cents: int) -> int:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id required")
        if type(amount_cents) is not int or not 0 < amount_cents <= 2**63 - 1:
            raise ValueError("amount_cents must be a positive signed 64-bit integer")
        with closing(sqlite3.connect(self.db_path, timeout=15)) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO transfers (request_id, amount_cents) VALUES (?, ?) "
                "ON CONFLICT(request_id) DO NOTHING", (request_id, amount_cents),
            )
            row = conn.execute(
                "SELECT id, amount_cents FROM transfers WHERE request_id = ?", (request_id,),
            ).fetchone()
            if row[1] != amount_cents:
                raise ValueError("request ID already used with different amount")
            return row[0]

    def count(self) -> int:
        with closing(sqlite3.connect(self.db_path)) as conn:
            return conn.execute("SELECT COUNT(*) FROM transfers").fetchone()[0]

    def total_cents(self) -> int:
        with closing(sqlite3.connect(self.db_path)) as conn:
            return conn.execute("SELECT COALESCE(SUM(amount_cents), 0) FROM transfers").fetchone()[0]
