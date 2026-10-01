from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ui.application.dto import Category, Direction
from ui.application.values import CategoryId


class CategoryReply(BaseModel):
    """응답 안의 카테고리 하나. 리포트·예산·카탈로그가 같은 모양을 쓴다."""

    id: str
    name: str
    direction: Literal["expense", "income"]

    def category(self) -> Category:
        return Category(CategoryId(self.id), self.name, Direction(self.direction))
