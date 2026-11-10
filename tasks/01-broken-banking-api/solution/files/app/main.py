"""Validate financial inputs before checking available funds."""
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI()


class Transfer(BaseModel):
    transaction_id: str
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2, allow_inf_nan=False)
    balance: Decimal = Field(ge=0, max_digits=14, decimal_places=2, allow_inf_nan=False)

    @field_validator("transaction_id")
    @classmethod
    def nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("transaction_id required")
        return value


@app.post("/transfer")
def transfer(data: Transfer):
    if data.amount > data.balance:
        raise HTTPException(status_code=409, detail="insufficient funds")
    remaining = data.balance - data.amount
    return {"transaction_id": data.transaction_id, "remaining_balance": float(remaining)}
