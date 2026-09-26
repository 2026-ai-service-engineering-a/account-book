from __future__ import annotations

from ui.application.dto import Direction


def test_values_match_the_api_contract():
    assert [d.value for d in Direction] == ["expense", "income"]
    assert Direction("income") is Direction.INCOME
