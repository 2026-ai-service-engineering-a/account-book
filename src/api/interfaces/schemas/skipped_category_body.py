from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.application.dto import SkippedCategory


class SkippedCategoryBody(BaseModel):
    """판정하지 않은 카테고리. short_history는 여섯 달이 안 됐고, too_few는 평소를 잴 거래가
    적다(api-contract 6장)."""

    category_id: str
    reason: Literal["short_history", "too_few"]

    @classmethod
    def of(cls, skipped: SkippedCategory) -> SkippedCategoryBody:
        return cls.model_validate({"category_id": skipped.category_id, "reason": skipped.reason})
