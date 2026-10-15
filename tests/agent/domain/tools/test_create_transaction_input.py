from __future__ import annotations

from datetime import datetime

import pytest

from agent.domain.tools import CreateTransactionInput
from agent.domain.values import CategoryId, Direction, Money, PaymentMethod


def test_a_naive_time_dies():
    with pytest.raises(ValueError, match="aware"):
        CreateTransactionInput(
            Direction.EXPENSE, Money(8500), datetime(2026, 10, 14, 12, 30),
            CategoryId("food"), PaymentMethod.CARD,
        )  # fmt: skip
