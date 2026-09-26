from __future__ import annotations

import pytest

from ui.application.values import Money


def test_only_whole_won():
    with pytest.raises(TypeError):
        Money(8500.0)  # type: ignore[arg-type]  # float가 들어오는 순간을 일부러 만든다
    with pytest.raises(TypeError):
        Money(True)


def test_arithmetic_keeps_currency():
    assert Money(8_500) + Money(1_500) == Money(10_000)
    assert Money(250_000) - Money(318_000) == Money(-68_000)
    assert -Money(5) == Money(-5) and abs(Money(-5)) == Money(5)
    assert Money.total([Money(1), Money(2), Money(3)]) == Money(6)
    assert Money.total([]) == Money(0)


def test_currencies_do_not_mix():
    with pytest.raises(ValueError):
        Money(1) + Money(1, "USD")


def test_format_truth_and_order():
    assert f"{Money(1_234_500):,}원" == "1,234,500원"
    assert f"{Money(32_300):+,}" == "+32,300"
    assert not Money(0) and Money(-1)
    assert Money(1) < Money(2)
