from __future__ import annotations

import pytest

from api.application.use_cases import CreateTransaction, UpdateTransaction
from api.domain.errors import ConfirmationRequired, TransactionNotFound
from api.domain.values import Money, Source, TransactionId
from tests.api.conftest import FakeUnitOfWork, draft

THRESHOLD = Money(100_000)


def test_changes_values_but_keeps_the_source():
    uow = FakeUnitOfWork()
    created = CreateTransaction(THRESHOLD)(uow, draft(), run_id="run-1", confirmed=False)
    updated = UpdateTransaction(THRESHOLD)(
        uow, created.id, draft(amount=9_000, category="cafe"), confirmed=False
    )
    assert updated.amount == Money(9_000) and updated.category_id == "cafe"
    assert updated.source is Source.AGENT and updated.run_id == "run-1"


def test_missing_is_not_found():
    with pytest.raises(TransactionNotFound):
        UpdateTransaction(THRESHOLD)(
            FakeUnitOfWork(), TransactionId("nope"), draft(), confirmed=True
        )


def test_big_amount_needs_a_confirmation():
    uow = FakeUnitOfWork()
    created = CreateTransaction(THRESHOLD)(uow, draft(), run_id=None, confirmed=False)
    with pytest.raises(ConfirmationRequired):
        UpdateTransaction(THRESHOLD)(uow, created.id, draft(amount=500_000), confirmed=False)
