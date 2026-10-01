from __future__ import annotations

from api.application.dto import PaceSeries
from api.domain.entities import Category
from api.domain.values import CategoryId, Direction, Money
from api.interfaces.schemas import PaceBody


def test_cumulative_as_whole_won():
    pace = PaceSeries(
        Category(CategoryId("food"), "식비", Direction.EXPENSE),
        Money(100),
        (Money(10), Money(30)),
        30,
        Money(450),
        None,
    )
    assert PaceBody.of(pace).cumulative == [10, 30]
