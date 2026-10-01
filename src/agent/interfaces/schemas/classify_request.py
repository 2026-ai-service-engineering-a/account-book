from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agent.domain.values import Direction


class ClassifyRequest(BaseModel):
    """`POST /classify`의 본문 — 카테고리 옆 AI 버튼. 금액·날짜는 받지 않는다(색인에 안 쓴다)."""

    merchant: str = Field(default="", max_length=100)
    memo: str = Field(default="", max_length=200)
    direction: Literal["expense", "income"]

    def direction_value(self) -> Direction:
        return Direction(self.direction)
