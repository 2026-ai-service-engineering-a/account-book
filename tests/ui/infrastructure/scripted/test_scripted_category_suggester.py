from __future__ import annotations

import asyncio

from ui.application.dto import Direction
from ui.infrastructure.scripted import ScriptedCategorySuggester


def test_keyword_hit_and_miss():
    suggester = ScriptedCategorySuggester()
    hit = asyncio.run(suggester.suggest("스타벅스 강남점", Direction.EXPENSE))
    assert hit is not None and hit.category_id == "cafe"
    assert "각본 대역" in hit.reason
    assert asyncio.run(suggester.suggest("알 수 없는 가게", Direction.EXPENSE)) is None


def test_respects_direction():
    suggester = ScriptedCategorySuggester()
    assert asyncio.run(suggester.suggest("급여", Direction.EXPENSE)) is None
