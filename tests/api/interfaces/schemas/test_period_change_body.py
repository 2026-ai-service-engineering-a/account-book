from __future__ import annotations

from api.application.dto import PeriodChange
from api.domain.entities import Category
from api.domain.values import CategoryId, Direction, Money
from api.interfaces.schemas import PeriodChangeBody

CAFE = Category(CategoryId("cafe"), "카페", Direction.EXPENSE)


def test_whole_won_with_signed_delta():
    body = PeriodChangeBody.of(PeriodChange(CAFE, Money(5_000), Money(4_000), Money(-1_000), 20))
    assert body.model_dump() == {
        "category": {"id": "cafe", "name": "카페", "direction": "expense"},
        "a": 5000,
        "b": 4000,
        "delta": -1000,
        "percent": 20,
    }
