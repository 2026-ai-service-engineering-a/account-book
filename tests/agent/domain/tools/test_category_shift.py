from __future__ import annotations

from agent.domain.tools import CategoryShift
from agent.domain.values import Amount, CategoryId


def test_delta_may_be_negative():
    cafe = CategoryId("cafe")
    shift = CategoryShift(cafe, "카페", Amount(53_500), Amount(6_300), Amount(-47_200), 88)
    assert shift.delta.amount < 0
