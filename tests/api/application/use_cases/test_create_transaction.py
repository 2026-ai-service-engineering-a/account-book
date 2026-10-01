from __future__ import annotations

import pytest

from api.application.use_cases import CreateTransaction
from api.domain.errors import ConfirmationRequired, InvalidTransaction
from api.domain.values import Money, Source, TransactionId
from tests.api.conftest import FakeUnitOfWork, draft

CREATE = CreateTransaction(Money(100_000), new_id=lambda: TransactionId("t-new"))


def test_adds_a_manual_transaction():
    uow = FakeUnitOfWork()
    created = CREATE(uow, draft(merchant="  김밥천국 "), run_id=None, confirmed=False)
    assert created.id == "t-new" and created.source is Source.MANUAL
    assert created.merchant == "김밥천국" and uow.transactions.rows["t-new"] == created


def test_run_id_marks_it_as_the_agents():
    created = CREATE(FakeUnitOfWork(), draft(), run_id="run-1", confirmed=False)
    assert created.source is Source.AGENT and created.run_id == "run-1"


def test_big_amount_needs_a_confirmation():
    with pytest.raises(ConfirmationRequired):
        CREATE(FakeUnitOfWork(), draft(amount=100_000), run_id=None, confirmed=False)
    assert CREATE(FakeUnitOfWork(), draft(amount=100_000), run_id=None, confirmed=True)


def test_validation_comes_before_the_confirmation():
    # 고칠 것이 있으면 확인을 묻기 전에 알려 준다
    with pytest.raises(InvalidTransaction):
        CREATE(
            FakeUnitOfWork(), draft(amount=200_000, category="nope"), run_id=None, confirmed=False
        )
