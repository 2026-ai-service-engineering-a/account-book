from __future__ import annotations

from ui.application.dto import Direction
from ui.infrastructure.api import CategoryReply


def test_becomes_a_ui_category():
    category = CategoryReply(id="food", name="식비", direction="expense").category()
    assert category.name == "식비" and category.direction is Direction.EXPENSE
