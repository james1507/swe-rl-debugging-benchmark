"""Intentionally buggy task environment. Do not fix in this directory."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Transfer(BaseModel):
    transaction_id: str
    amount: float
    balance: float

@app.post("/transfer")
def transfer(data: Transfer):
    if data.amount < 0:  # BUG: zero amount accepted
        return {"error": "invalid amount"}  # BUG: HTTP 200 instead of 422
    if data.amount > data.balance:
        return {"error": "insufficient funds"}  # BUG: HTTP 200 instead of 409
    return {"transaction_id": data.transaction_id, "remaining_balance": round(data.balance-data.amount, 2)}
