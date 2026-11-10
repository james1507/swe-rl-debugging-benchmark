"""Buggy SQLite banking transaction store: replays create duplicate rows."""
import sqlite3
from pathlib import Path

class TransactionRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY, request_id TEXT, amount_cents INTEGER)")

    def transfer(self, request_id: str, amount_cents: int) -> int:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.execute("INSERT INTO transfers(request_id,amount_cents) VALUES(?,?)", (request_id,amount_cents))
            return cursor.lastrowid

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM transfers").fetchone()[0]

    def total_cents(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COALESCE(SUM(amount_cents),0) FROM transfers").fetchone()[0]
