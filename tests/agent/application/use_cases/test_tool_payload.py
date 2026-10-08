from __future__ import annotations

from datetime import date, datetime

from agent.application.use_cases.tool_payload import MAX_BYTES, fit, plain
from agent.domain.tools import BudgetLine, SuggestedCategory
from agent.domain.values import Amount, CategoryId, Confidence, Direction
from tests.agent.conftest import SEOUL


def test_money_keeps_its_currency_and_no_formatting():
    over_on = date(2026, 9, 28)
    line = BudgetLine(
        CategoryId("food"), "식비", Amount(182_300), Amount(300_000), None, 61, None, over_on
    )
    assert plain(line) == {
        "category_id": "food",
        "name": "식비",
        "spent": {"amount": 182300, "currency": "KRW"},
        "limit": {"amount": 300000, "currency": "KRW"},
        "remaining": None,
        "percent": 61,
        "projected": None,
        "over_on": "2026-09-28",
    }


def test_values_and_containers():
    assert plain(SuggestedCategory(CategoryId("cafe"), Confidence(0.9))) == {
        "category_id": "cafe",
        "confidence": 0.9,
    }
    assert plain((Direction.INCOME, datetime(2026, 10, 1, 9, tzinfo=SEOUL))) == [
        "income",
        "2026-10-01T09:00:00+09:00",
    ]


def test_fit_drops_rows_from_the_end_until_it_fits():
    data: dict[str, object] = {"rows": ["가" * 100 for _ in range(100)]}
    assert fit(data, "rows")
    rows = data["rows"]
    assert isinstance(rows, list) and 0 < len(rows) < 100
    assert len(str(data).encode()) <= MAX_BYTES + 200


def test_small_data_is_untouched():
    data: dict[str, object] = {"rows": [1, 2, 3]}
    assert not fit(data, "rows") and data == {"rows": [1, 2, 3]}
