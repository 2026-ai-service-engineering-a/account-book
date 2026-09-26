from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from ui.application.dto import Direction, Proposal
from ui.application.values import Money, ProposalId


def make() -> Proposal:
    return Proposal(
        ProposalId("p1"),
        date(2026, 9, 16),
        "식비",
        Direction.EXPENSE,
        Money(8_500),
        "카드",
        "김밥천국",
    )


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.amount = Money(1)  # type: ignore[misc]
