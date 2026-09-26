from __future__ import annotations

from typing import Protocol

from ui.application.dto import CategorySuggestion, Direction


class CategorySuggester(Protocol):
    """AI 자리 ② — 가맹점명을 보고 사람이 고르던 카테고리를 대신 고른다.

    진짜는 api의 `POST /v1/categories/suggest`(규칙 테이블 → LLM). 지금은 각본 대역.
    """

    async def suggest(self, merchant: str, direction: Direction) -> CategorySuggestion | None: ...
