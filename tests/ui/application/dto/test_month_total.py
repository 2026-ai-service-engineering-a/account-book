from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import MonthTotal, Period
from ui.application.values import Money


def make() -> MonthTotal:
    return MonthTotal(Period(2026, 9), Money(1), Money(2))


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.expense = Money(0)  # type: ignore[misc]
