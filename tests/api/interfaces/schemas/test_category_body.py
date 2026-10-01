from __future__ import annotations

from api.domain.entities import Category
from api.domain.values import CategoryId, Direction
from api.interfaces.schemas import CategoryBody


def test_shape():
    body = CategoryBody.of(Category(CategoryId("food"), "식비", Direction.EXPENSE))
    assert body.model_dump() == {"id": "food", "name": "식비", "direction": "expense"}
