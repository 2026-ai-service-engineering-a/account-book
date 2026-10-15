from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import CategoryId


@dataclass(frozen=True, slots=True)
class SkippedCategory:
    """판정하지 않은 카테고리와 그 이유(short_history · too_few). 조용히 빼지 않는다 —
    "특이한 건이 없다"와 "판정할 수 없다"는 다른 답이다."""

    category_id: CategoryId
    reason: str
