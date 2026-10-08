from __future__ import annotations

from datetime import datetime

from api.application.dto import Totals
from api.application.use_cases import SummarizeSpending
from api.domain.values import CategoryId, Money, Period, TimeRange
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL


def test_sums_inside_the_month_only():
    summarize = SummarizeSpending(ledger(), SEOUL)
    assert summarize(period=Period(2026, 9)) == Totals(Money(185_000), Money(3_000_000))
    assert summarize(period=Period(2026, 9), category_id=CategoryId("food")).expense == Money(
        180_000
    )
    assert summarize().expense == Money(219_000)  # 기간 없이 전부


def test_range_instead_of_a_month():
    # 9월 1일~2일만: 식비 100,000 + 80,000. 3일의 카페는 빠진다
    two_days = TimeRange(datetime(2026, 9, 1, tzinfo=SEOUL), datetime(2026, 9, 3, tzinfo=SEOUL))
    assert SummarizeSpending(ledger(), SEOUL)(period=two_days).expense == Money(180_000)
