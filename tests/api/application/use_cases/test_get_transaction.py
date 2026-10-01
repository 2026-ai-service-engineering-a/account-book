from __future__ import annotations

import pytest

from api.application.use_cases import CreateTransaction, GetTransaction
from api.domain.errors import TransactionNotFound
from api.domain.values import Money, TransactionId
from tests.api.conftest import FakeUnitOfWork, draft


def test_finds_or_raises():
    uow = FakeUnitOfWork()
    created = CreateTransaction(Money(100_000))(uow, draft(), run_id=None, confirmed=False)
    assert GetTransaction(uow)(created.id) == created
    with pytest.raises(TransactionNotFound):
        GetTransaction(uow)(TransactionId("nope"))
