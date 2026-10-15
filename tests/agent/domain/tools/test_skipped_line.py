from __future__ import annotations

from agent.domain.tools import SkippedLine
from agent.domain.values import CategoryId


def test_names_the_category_and_why():
    assert SkippedLine(CategoryId("cafe"), "short_history").reason == "short_history"
