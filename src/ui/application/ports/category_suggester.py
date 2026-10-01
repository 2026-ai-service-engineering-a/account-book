from __future__ import annotations

from typing import Protocol

from ui.application.dto import CategorySuggestion, Direction


class CategorySuggester(Protocol):
    """AI 자리 ② — 가맹점·메모를 보고 사람이 고르던 카테고리를 대신 고른다.

    진짜는 agent의 `POST /classify`(규칙 → 이력 → 벡터 이웃 → 애매하면 LLM). 고르지 못해도
    예외를 내지 않는다 — 이유를 담아 `category_id=None`으로 돌려준다.
    """

    async def suggest(
        self, merchant: str, memo: str, direction: Direction
    ) -> CategorySuggestion: ...
