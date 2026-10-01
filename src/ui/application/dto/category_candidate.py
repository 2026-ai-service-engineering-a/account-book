from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import CategoryId


@dataclass(frozen=True, slots=True)
class CategoryCandidate:
    category_id: CategoryId
    confidence: float  # 0~1. 검색이 계산한 값이다 — 모델의 자기 확신이 아니다

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"신뢰도는 0~1이다: {self.confidence}")
