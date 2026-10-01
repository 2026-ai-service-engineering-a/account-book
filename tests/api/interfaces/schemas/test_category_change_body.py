from __future__ import annotations

from api.application.dto import CategoryChange
from api.domain.entities import Category
from api.domain.values import CategoryId, Direction, Money
from api.interfaces.schemas import CategoryChangeBody

FOOD = Category(CategoryId("food"), "식비", Direction.EXPENSE)


def test_first_month_has_nulls():
    body = CategoryChangeBody.of(CategoryChange(FOOD, Money(100), None, None, None)).model_dump()
    assert body["this_month"] == 100 and body["last_month"] is None and body["delta"] is None
