# Task 03 — Prevent duplicate banking transactions

## Situation

A SQLite repository inserts one row on every request, including retries. Concurrent requests with the same `request_id` create duplicate transfers and inflate totals. Repair `app/repository.py`.

## Public interface to preserve

```python
TransactionRepository(db_path: str | Path)
transfer(request_id: str, amount_cents: int) -> int
count() -> int
total_cents() -> int
```

## Contract

- `request_id`: nonblank string. Whitespace-only strings and non-string values raise `ValueError`. Treat valid IDs as opaque data; do not interpolate them into SQL.
- `amount_cents`: Python integer from `1` through `2**63 - 1`. Reject booleans, floats, strings, null, zero, negative and out-of-range values with `ValueError` before writing.
- First valid request inserts one transfer and returns its positive numeric database ID.
- Replaying the same ID and amount returns the **original ID**, with no additional row or change to totals.
- Reusing an ID with a different amount raises `ValueError`, preserving existing data and allowing later valid requests.
- Concurrent same-key retries must produce exactly one row, including callers using separate repository instances and separate Python processes.
- Concurrent different keys must all persist, with distinct numeric IDs and correct totals.
- Enforce request-key uniqueness in SQLite itself. An in-memory lock or cache alone is insufficient.
- Use atomic SQL transactions. Conflicting concurrent amounts may choose either first writer; all accepted retries must agree with the committed amount.
- Closing and reopening the repository must preserve replay behavior.

## Scope and bounds

Each evaluation starts with a fresh on-disk database. Migration or deduplication of pre-existing legacy schemas is outside scope. Tests keep aggregate totals within SQLite's signed 64-bit integer range. No HTTP endpoint, external database, payment provider or distributed lock is needed.

Use `sqlite3` from Python standard library. Do not alter the public method signatures or evaluator tests. Avoid leaking connections or leaving a write transaction open after an exception.

## Evaluation

Verifier covers validation without writes, sequential retries, persistence, thread/process concurrency, mixed-amount races, SQL uniqueness, boundary amounts and SQL-special identifiers. Every verifier case must pass.
