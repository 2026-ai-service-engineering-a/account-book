from __future__ import annotations

from datetime import datetime

from api.application.dto import Frequency
from api.application.use_cases import CountFrequency
from api.domain.values import CategoryId, Direction, Money, TimeRange
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL

SEPTEMBER = TimeRange(datetime(2026, 9, 1, tzinfo=SEOUL), datetime(2026, 10, 1, tzinfo=SEOUL))


def test_counts_expenses_and_the_days_they_fell_on():
    count = CountFrequency(ledger())
    assert count(SEPTEMBER, category_id=CategoryId("food")) == Frequency(2, 2, 1.0, Money(90_000))
    # 지출이 기본이다 — 9월 10일의 급여는 세지 않는다
    assert count(SEPTEMBER) == Frequency(3, 3, 1.0, Money(61_667))


def test_income_when_asked():
    assert CountFrequency(ledger())(SEPTEMBER, direction=Direction.INCOME) == Frequency(
        1, 1, None, Money(3_000_000)
    )


def test_text_filter_is_trimmed_like_the_summary():
    found = CountFrequency(ledger())(SEPTEMBER, text="  김밥  ")
    assert found.count == 3


def test_nothing_in_the_range_is_zero_not_an_error():
    october = TimeRange(datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 11, 1, tzinfo=SEOUL))
    assert CountFrequency(ledger())(october) == Frequency(0, 0, None, None)
