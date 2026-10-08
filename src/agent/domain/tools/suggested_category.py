from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Confidence


@dataclass(frozen=True, slots=True)
class SuggestedCategory:
    category_id: CategoryId
    confidence: Confidence  # 검색이 계산한 값. 모델이 말한 확신이 아니다
