from __future__ import annotations

from agent.domain.tools import CategoryLine, CategorySuggestion
from agent.domain.values import CategoryId


def test_no_candidates_still_carries_the_dictionary():
    found = CategorySuggestion("none", (), (), (CategoryLine(CategoryId("food"), "식비"),))
    assert found.candidates == () and len(found.categories) == 1
