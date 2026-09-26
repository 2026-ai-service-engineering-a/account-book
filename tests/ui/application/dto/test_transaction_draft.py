from __future__ import annotations

import dataclasses

import pytest

from tests.ui.conftest import NOW
from ui.application.dto import Direction, TransactionDraft
from ui.application.values import AccountId, CategoryId, Money


def make() -> TransactionDraft:
    return TransactionDraft(
        Direction.EXPENSE, Money(8_500), NOW, CategoryId("food"), AccountId("card")
    )


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.amount = Money(1)  # type: ignore[misc]
