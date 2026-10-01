from __future__ import annotations

import asyncio

from ui.application.dto import Direction
from ui.infrastructure.scripted import ScriptedCategorySuggester


def test_keyword_hit_and_miss():
    suggester = ScriptedCategorySuggester()
    hit = asyncio.run(suggester.suggest("스타벅스 강남점", "", Direction.EXPENSE))
    assert hit.category_id == "cafe" and "각본 대역" in hit.reason and not hit.by_llm
    miss = asyncio.run(suggester.suggest("알 수 없는 가게", "", Direction.EXPENSE))
    assert miss.category_id is None and miss.reason  # 못 골라도 이유는 말한다


def test_reads_the_memo_too():
    hit = asyncio.run(ScriptedCategorySuggester().suggest("", "점심 김밥", Direction.EXPENSE))
    assert hit.category_id == "food"


def test_respects_direction():
    suggester = ScriptedCategorySuggester()
    assert asyncio.run(suggester.suggest("급여", "", Direction.EXPENSE)).category_id is None
