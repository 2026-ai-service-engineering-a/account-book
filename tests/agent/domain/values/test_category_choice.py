from __future__ import annotations

import pytest

from agent.domain.values import CategoryChoice, CategoryId, ChoiceStrategy


def test_abstain_has_no_category():
    choice = CategoryChoice.abstain("근거가 없어요")
    assert choice.category_id is None and choice.strategy is ChoiceStrategy.NONE


def test_none_strategy_and_empty_category_go_together():
    with pytest.raises(ValueError):
        CategoryChoice(CategoryId("cafe"), ChoiceStrategy.NONE, "x")
    with pytest.raises(ValueError):
        CategoryChoice(None, ChoiceStrategy.LLM, "x")
