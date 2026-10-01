from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import CategorySuggestion
from ui.application.values import CategoryId


def make() -> CategorySuggestion:
    return CategorySuggestion(CategoryId("cafe"), "각본 대역")


def test_is_a_frozen_value():
    # 화면으로 넘어간 뒤에 값이 바뀌면 같은 줄이 두 가지로 그려진다
    value = make()
    assert value == make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        value.category_id = CategoryId("food")  # type: ignore[misc]


def test_may_carry_no_category_but_still_a_reason():
    # 못 골라도 왜 못 골랐는지는 화면에 보인다
    value = CategorySuggestion(None, "고를 만한 근거가 없어요.")
    assert value.category_id is None and not value.by_llm
