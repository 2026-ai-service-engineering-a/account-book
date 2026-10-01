from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agent.domain.values import CategoryChoice


class CategoryChoiceBody(BaseModel):
    """고른 카테고리. `category_id`가 null이면 고르지 않았고, 셀렉트는 그대로 둔다.

    `reason`은 화면에 보일 근거 한 줄이다. `strategy`가 llm이면 화면이 AI 표시를 붙인다.
    """

    category_id: str | None
    strategy: Literal["rule", "history", "vector", "llm", "none"]
    reason: str

    @classmethod
    def of(cls, choice: CategoryChoice) -> CategoryChoiceBody:
        return cls(
            category_id=choice.category_id, strategy=choice.strategy.value, reason=choice.reason
        )
