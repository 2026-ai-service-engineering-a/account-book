from __future__ import annotations

import pytest

from api.application.use_cases import CreateTransaction, DeleteTransaction
from api.domain.errors import ConfirmationRequired, TransactionNotFound
from api.domain.values import Money, TransactionId
from tests.api.conftest import FakeUnitOfWork, draft


def test_always_needs_a_confirmation_even_for_small_amounts():
    uow = FakeUnitOfWork()
    created = CreateTransaction(Money(100_000))(uow, draft(amount=1), run_id=None, confirmed=False)
    with pytest.raises(ConfirmationRequired):
        DeleteTransaction()(uow, created.id, confirmed=False)
    DeleteTransaction()(uow, created.id, confirmed=True)
    assert created.id not in uow.transactions.rows


def test_missing_is_not_found():
    with pytest.raises(TransactionNotFound):
        DeleteTransaction()(FakeUnitOfWork(), TransactionId("nope"), confirmed=True)
