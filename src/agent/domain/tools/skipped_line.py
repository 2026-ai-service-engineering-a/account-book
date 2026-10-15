from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId


@dataclass(frozen=True, slots=True)
class SkippedLine:
    """판정하지 않은 카테고리. short_history는 여섯 달이 안 됐고, too_few는 거래가 적다."""

    category_id: CategoryId
    reason: str
