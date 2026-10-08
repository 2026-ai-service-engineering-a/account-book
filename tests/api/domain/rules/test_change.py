from __future__ import annotations

from api.domain.rules import change
from api.domain.values import Money


def test_percent_is_absolute_and_whole():
    assert change.percent(Money(30_000), Money(180_000)) == 500
    assert change.percent(Money(200), Money(100)) == 50  # 줄어도 양수. 방향은 증감 금액이 말한다
    assert change.percent(Money(3), Money(4)) == 33


def test_no_percent_from_zero():
    assert change.percent(Money(0), Money(5_000)) is None
