from concurrent.futures import ThreadPoolExecutor
import sqlite3
import subprocess
import sys

import pytest

from app.repository import TransactionRepository


@pytest.fixture
def repo(tmp_path):
    return TransactionRepository(tmp_path / "bank.db")


def test_single_transfer(repo):
    assert repo.transfer("request-1", 1250) > 0
    assert repo.count() == 1
    assert repo.total_cents() == 1250


def test_retry_is_idempotent(repo):
    first = repo.transfer("request-1", 1250)
    assert repo.transfer("request-1", 1250) == first
    assert repo.count() == 1
    assert repo.total_cents() == 1250


def test_concurrent_retries_are_idempotent(repo):
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(lambda _: repo.transfer("same-request", 500), range(32)))
    assert len(set(ids)) == 1
    assert repo.count() == 1
    assert repo.total_cents() == 500


def test_distinct_requests(repo):
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(lambda i: repo.transfer(f"request-{i}", 100), range(32)))
    assert len(set(ids)) == 32
    assert repo.count() == 32
    assert repo.total_cents() == 3200


def test_replay_with_different_amount_fails_without_data_loss(repo):
    first = repo.transfer("request-1", 100)
    with pytest.raises(ValueError):
        repo.transfer("request-1", 200)
    assert repo.transfer("request-1", 100) == first
    repo.transfer("request-2", 50)
    assert repo.count() == 2
    assert repo.total_cents() == 150


@pytest.mark.parametrize("request_id", ["", " ", "\t\n", None, 123, True])
def test_invalid_request_id(repo, request_id):
    with pytest.raises(ValueError):
        repo.transfer(request_id, 100)
    assert repo.count() == 0


@pytest.mark.parametrize("amount", [0, -100, 1.5, "100", None, True, False, 2**63])
def test_invalid_amount(repo, amount):
    with pytest.raises(ValueError):
        repo.transfer("request-1", amount)
    assert repo.count() == 0


def test_persistence_across_instances(repo):
    first = repo.transfer("persistent", 100)
    reopened = TransactionRepository(repo.db_path)
    assert reopened.transfer("persistent", 100) == first
    assert reopened.count() == 1
    assert reopened.total_cents() == 100


def test_concurrent_retries_from_separate_processes(repo):
    program = (
        "from app.repository import TransactionRepository; import sys; "
        "r = TransactionRepository(sys.argv[1]); "
        "print(r.transfer('process-retry', 500))"
    )

    def transfer(_):
        result = subprocess.run(
            [sys.executable, "-c", program, repo.db_path],
            capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, result.stderr
        return int(result.stdout.strip())

    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(transfer, range(16)))
    assert len(set(ids)) == 1
    assert repo.count() == 1
    assert repo.total_cents() == 500


def test_conflicting_concurrent_retries(repo):
    def transfer(amount):
        try:
            return repo.transfer("conflict", amount), amount
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(transfer, [100, 200] * 8))
    accepted = [result for result in results if result is not None]
    assert accepted
    assert any(result is None for result in results)
    assert len(set(accepted)) == 1
    assert repo.count() == 1
    assert repo.total_cents() == accepted[0][1]


def test_unique_constraint_protects_direct_writes(repo):
    repo.transfer("request-1", 100)
    with sqlite3.connect(repo.db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO transfers(request_id, amount_cents) VALUES (?, ?)",
                ("request-1", 100),
            )
    assert repo.count() == 1


def test_largest_supported_amount(repo):
    first = repo.transfer("large", 2**63 - 1)
    assert repo.transfer("large", 2**63 - 1) == first
    assert repo.total_cents() == 2**63 - 1


def test_identifier_with_sql_characters_is_data(repo):
    key = "'); DROP TABLE transfers; --"
    first = repo.transfer(key, 100)
    assert repo.transfer(key, 100) == first
    assert repo.count() == 1
