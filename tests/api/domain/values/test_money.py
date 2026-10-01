from __future__ import annotations

import pytest

from api.domain.values import Money


def test_whole_won_only():
    with pytest.raises(TypeError):
        Money(8500.0)  # type: ignore[arg-type]  # float가 섞이면 만드는 순간 죽는다


def test_adds_subtracts_and_orders():
    assert Money(8500) + Money(1500) == Money(10_000)
    assert Money(1000) - Money(1500) == Money(-500)  # 증감은 음수가 될 수 있다
    assert Money(100_000) >= Money(100_000) > Money(99_999)
    assert Money.total([Money(1), Money(2)]) == Money(3)
