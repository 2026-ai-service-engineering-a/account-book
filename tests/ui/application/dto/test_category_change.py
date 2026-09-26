from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import Category, CategoryChange, Direction
from ui.application.values import CategoryId, Money


def make() -> CategoryChange:
    return CategoryChange(
        Category(CategoryId("food"), "식비", Direction.EXPENSE), Money(1), None, None, None
    )


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.this_month = Money(2)  # type: ignore[misc]
