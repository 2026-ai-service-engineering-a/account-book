from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import Category, Direction, PaceSeries
from ui.application.values import CategoryId, Money


def make() -> PaceSeries:
    return PaceSeries(
        Category(CategoryId("food"), "식비", Direction.EXPENSE),
        Money(300_000),
        (Money(1),),
        30,
        Money(30),
        None,
    )


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.limit = Money(0)  # type: ignore[misc]
