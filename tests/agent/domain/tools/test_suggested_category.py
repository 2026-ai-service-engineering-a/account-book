from __future__ import annotations

from agent.domain.tools import SuggestedCategory
from agent.domain.values import CategoryId, Confidence


def test_holds_the_searchs_confidence():
    assert SuggestedCategory(CategoryId("food"), Confidence(0.94)).confidence.value == 0.94
