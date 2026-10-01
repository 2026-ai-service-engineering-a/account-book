from __future__ import annotations

import pytest

from ui.infrastructure.memory.searchable_text import searchable_text, text_hash


@pytest.mark.parametrize(
    ("merchant", "memo", "expected"),
    [
        ("김밥천국 강남점", "점심", "김밥천국 점심"),
        ("투썸플레이스 2호점", "", "투썸플레이스"),
        ("(주)이마트", "", "이마트"),
        ("편의점", "", "편의점"),  # 붙은 "점"은 이름이다
        ("  스타벅스   ", "  아아 ", "스타벅스 아아"),
        ("", "", ""),
    ],
)
def test_normalizes(merchant, memo, expected):
    assert searchable_text(merchant, memo) == expected


def test_same_text_same_hash():
    assert text_hash("스타벅스") == text_hash("스타벅스") != text_hash("메가커피")
