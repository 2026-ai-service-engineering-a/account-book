from __future__ import annotations

from typing import TypedDict

from pydantic import RootModel

from agent.domain.tools import CategoryLine
from agent.domain.values import CategoryId


class _Category(TypedDict):
    id: str
    name: str


class CategoriesReply(RootModel[list[_Category]]):
    """api `GET /v1/categories`의 응답 본문 — 카테고리 사전."""

    def lines(self) -> tuple[CategoryLine, ...]:
        return tuple(CategoryLine(CategoryId(c["id"]), c["name"]) for c in self.root)
