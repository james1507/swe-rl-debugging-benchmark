# Task 01 — Repair a banking transfer API

## Situation

`POST /transfer` currently accepts invalid inputs and reports failed transfers with HTTP 200. Financial subtraction uses binary floating point. Repair `app/main.py` while preserving the endpoint and request/response field names.

## Contract

Request is a JSON object with three required fields:

| Field | Accepted values |
|---|---|
| `transaction_id` | Nonblank string; whitespace-only strings are invalid. Preserve supplied valid identifier. |
| `amount` | Finite decimal amount strictly greater than zero. JSON number or decimal string. |
| `balance` | Finite decimal balance greater than or equal to zero. JSON number or decimal string. |

Amounts and balances allow at most 12 integral digits and 2 fractional digits, with maximum `999999999999.99`. Trailing zeros do not add precision (`"0.100"` is valid); `"0.001"` is invalid. Reject booleans, null, missing fields, arrays, objects, nonnumeric strings and nonfinite values with HTTP **422**.

Validate the entire request **before** comparing amount with balance. A transfer of `"100.001"` against `"100"` is a validation error (422), not insufficient funds.

- Valid transfer: HTTP **200**, exactly `{"transaction_id": "<supplied ID>", "remaining_balance": <JSON number>}`.
- Insufficient funds on an otherwise valid request: HTTP **409**.
- Exact-balance transfer: valid, remaining balance zero.
- Calculate using decimal arithmetic. Example: `"0.30" - "0.10"` produces numeric `0.2`.
- Error-body wording is not graded.

## Scope

This is a stateless validation exercise. No database, authentication, real payment integration or persistent balance is required. Use installed dependencies; do not edit evaluator-owned Dockerfile, requirements, or verifier tests.

## Example

```json
{"transaction_id": "tx-100", "amount": "35.25", "balance": "100.00"}
```

Expected HTTP 200:

```json
{"transaction_id": "tx-100", "remaining_balance": 64.75}
```

## Evaluation

Verifier checks valid transfers, required fields, types, bounds, decimal precision, status codes and validation precedence. All verifier cases must pass. A failing test is not permission to remove or skip it.
