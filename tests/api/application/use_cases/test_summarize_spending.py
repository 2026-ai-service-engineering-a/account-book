from __future__ import annotations

from api.application.dto import Totals
from api.application.use_cases import SummarizeSpending
from api.domain.values import CategoryId, Money, Period
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL


def test_sums_inside_the_month_only():
    summarize = SummarizeSpending(ledger(), SEOUL)
    assert summarize(period=Period(2026, 9)) == Totals(Money(185_000), Money(3_000_000))
    assert summarize(period=Period(2026, 9), category_id=CategoryId("food")).expense == Money(
        180_000
    )
    assert summarize().expense == Money(219_000)  # 기간 없이 전부
