from __future__ import annotations

from api.application.dto import Frequency
from api.domain.values import Money
from api.interfaces.schemas import FrequencyBody


def test_whole_won_and_nulls_when_nothing_counted():
    assert FrequencyBody.of(Frequency(7, 5, 1.4, Money(5_200))).model_dump() == {
        "count": 7,
        "day_count": 5,
        "avg_gap_days": 1.4,
        "avg_amount": 5200,
    }
    empty = FrequencyBody.of(Frequency(0, 0, None, None)).model_dump()
    assert empty["avg_gap_days"] is None and empty["avg_amount"] is None
