from decimal import Decimal

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def request(amount, balance="100.00", transaction_id="tx-100"):
    return client.post("/transfer", json={
        "transaction_id": transaction_id, "amount": amount, "balance": balance,
    })


@pytest.mark.parametrize("amount,balance,remaining", [
    ("35.25", "100.00", "64.75"),
    ("0.10", "0.30", "0.20"),
    ("100.00", "100.00", "0"),
    (35.25, 100, "64.75"),
    ("0.100", "0.300", "0.20"),
    ("0.01", "999999999999.99", "999999999999.98"),
])
def test_valid_transfer(amount, balance, remaining):
    response = request(amount, balance)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"transaction_id", "remaining_balance"}
    assert data["transaction_id"] == "tx-100"
    assert isinstance(data["remaining_balance"], (int, float))
    assert Decimal(str(data["remaining_balance"])) == Decimal(remaining)


@pytest.mark.parametrize("amount", [
    "0", "-1", "0.001", "NaN", "Infinity", "-Infinity", "abc", "", None,
    True, False, [], {}, "1000000000000", "1e1000",
])
def test_invalid_amount(amount):
    assert request(amount).status_code == 422


@pytest.mark.parametrize("balance", [
    "-0.01", "0.001", "NaN", "Infinity", "-Infinity", "abc", "", None,
    True, [], {}, "1000000000000", "1e1000",
])
def test_invalid_balance(balance):
    assert request("0.01", balance).status_code == 422


@pytest.mark.parametrize("transaction_id", ["", " ", "\t\n", None, 123, True])
def test_invalid_identifier(transaction_id):
    assert request("10", transaction_id=transaction_id).status_code == 422


@pytest.mark.parametrize("field", ["amount", "balance", "transaction_id"])
def test_required_fields(field):
    payload = {"amount": "1", "balance": "100", "transaction_id": "tx-1"}
    del payload[field]
    assert client.post("/transfer", json=payload).status_code == 422


@pytest.mark.parametrize("amount,balance", [("150", "100"), ("0.01", "0")])
def test_insufficient_funds(amount, balance):
    assert request(amount, balance).status_code == 409


def test_validation_precedes_insufficient_funds():
    assert request("100.001", "100").status_code == 422
