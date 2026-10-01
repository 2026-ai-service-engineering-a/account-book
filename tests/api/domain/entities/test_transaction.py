from __future__ import annotations

from datetime import datetime

import pytest

from api.domain.entities import Transaction
from api.domain.values import AccountId, CategoryId, Direction, Money, Source, TransactionId


def test_time_must_be_aware():
    with pytest.raises(ValueError):
        Transaction(
            id=TransactionId("t1"),
            direction=Direction.EXPENSE,
            amount=Money(8500),
            occurred_at=datetime(2026, 9, 16, 12, 30),
            category_id=CategoryId("food"),
            account_id=AccountId("card"),
            merchant="",
            memo="",
            source=Source.MANUAL,
        )
