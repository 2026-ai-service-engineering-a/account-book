from __future__ import annotations

from api.application.dto import SkippedCategory
from api.domain.values import CategoryId


def test_carries_the_reason():
    assert SkippedCategory(CategoryId("cafe"), "short_history").reason == "short_history"
