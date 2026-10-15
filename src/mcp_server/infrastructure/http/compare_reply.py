from __future__ import annotations

from typing import TypedDict

from pydantic import RootModel

from .amounts import amount


class _Category(TypedDict):
    id: str
    name: str


class _Change(TypedDict):
    category: _Category
    a: int
    b: int
    delta: int
    percent: int | None


class CompareReply(RootModel[list[_Change]]):
    """api `GET /v1/stats/compare`의 응답 본문 — 카테고리별 줄의 목록."""

    def rows(self) -> list[dict[str, object]]:
        return [
            {
                "category_id": c["category"]["id"],
                "name": c["category"]["name"],
                "a": amount(c["a"]),
                "b": amount(c["b"]),
                "delta": amount(c["delta"]),
                "percent": c["percent"],
            }
            for c in self.root
        ]
