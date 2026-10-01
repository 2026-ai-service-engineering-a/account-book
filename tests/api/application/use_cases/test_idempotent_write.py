from __future__ import annotations

import pytest

from api.application.dto import StoredReply
from api.application.errors import IdempotencyKeyReused, RequestInProgress
from api.application.use_cases import IdempotentWrite
from api.domain.errors import InvalidTransaction
from tests.api.conftest import FakeUnitOfWork


def counting(reply: StoredReply):
    calls = []

    def perform(uow):
        calls.append(1)
        return reply

    return perform, calls


def test_first_time_runs_and_stores_then_replays():
    uow = FakeUnitOfWork()
    perform, calls = counting(StoredReply(201, {"id": "t1"}))
    write = IdempotentWrite(uow)
    assert write("k1", "h1", perform) == StoredReply(201, {"id": "t1"})
    assert write("k1", "h1", perform) == StoredReply(201, {"id": "t1"})
    assert len(calls) == 1 and uow.commits == 1  # 두 번째는 다시 실행하지 않는다


def test_same_key_different_body_is_refused():
    uow = FakeUnitOfWork()
    perform, _ = counting(StoredReply(201, {}))
    IdempotentWrite(uow)("k1", "h1", perform)
    with pytest.raises(IdempotencyKeyReused):
        IdempotentWrite(uow)("k1", "h2", perform)


def test_unfinished_key_is_in_progress():
    uow = FakeUnitOfWork()
    uow.idempotency.claim("k1", "h1")
    with pytest.raises(RequestInProgress):
        IdempotentWrite(uow)("k1", "h1", counting(StoredReply(201))[0])


def test_failure_leaves_no_key_so_a_fixed_retry_with_the_same_key_works():
    # 화면은 폼을 열 때 만든 키 하나로 고쳐서 다시 보낸다(transaction-form.md 4.2)
    uow = FakeUnitOfWork()

    def invalid(_):
        raise InvalidTransaction({"amount": "금액"})

    with pytest.raises(InvalidTransaction):
        IdempotentWrite(uow)("k1", "h1", invalid)
    assert uow.idempotency.find("k1") is None
    assert IdempotentWrite(uow)("k1", "h2", counting(StoredReply(201))[0]).status_code == 201
