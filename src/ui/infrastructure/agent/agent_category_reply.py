from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ui.application.dto import CategorySuggestion
from ui.application.values import CategoryId


class AgentCategoryReply(BaseModel):
    """agent가 고른 카테고리 — `POST /classify`의 본문이자 `/capture` 응답의 `category`."""

    category_id: str | None
    strategy: Literal["rule", "history", "vector", "llm", "none"]
    reason: str

    def suggestion(self) -> CategorySuggestion:
        category = CategoryId(self.category_id) if self.category_id else None
        return CategorySuggestion(category, self.reason, by_llm=self.strategy == "llm")
