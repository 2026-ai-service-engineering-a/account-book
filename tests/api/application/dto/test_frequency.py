from __future__ import annotations

from api.application.dto import Frequency
from api.domain.values import Money


def test_nothing_counted_has_no_average():
    empty = Frequency(count=0, day_count=0, avg_gap_days=None, avg_amount=None)
    assert empty.avg_amount is None  # "평균 0원"이 아니다
    assert Frequency(7, 5, 1.4, Money(5_200)).day_count == 5
