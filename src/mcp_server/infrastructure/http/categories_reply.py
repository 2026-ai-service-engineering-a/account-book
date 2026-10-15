from __future__ import annotations

from typing import TypedDict

from pydantic import RootModel


class _Category(TypedDict):
    id: str
    name: str


class CategoriesReply(RootModel[list[_Category]]):
    """api `GET /v1/categories`의 응답 본문 — 카테고리 사전. 방향은 읽지 않는다."""

    def rows(self) -> list[dict[str, object]]:
        return [{"id": c["id"], "name": c["name"]} for c in self.root]
