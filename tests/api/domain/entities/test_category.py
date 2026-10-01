from __future__ import annotations

from api.domain.entities import Category
from api.domain.values import CategoryId, Direction


def test_belongs_to_a_direction():
    assert Category(CategoryId("food"), "식비", Direction.EXPENSE).direction is Direction.EXPENSE
