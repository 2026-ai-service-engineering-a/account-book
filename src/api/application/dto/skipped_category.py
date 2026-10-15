from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import CategoryId, SkipReason


@dataclass(frozen=True, slots=True)
class SkippedCategory:
    """판정하지 않은 카테고리와 그 이유. 조용히 빼지 않는다."""

    category_id: CategoryId
    reason: SkipReason
