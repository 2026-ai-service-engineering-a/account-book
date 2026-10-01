from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId


@dataclass(frozen=True, slots=True)
class CategoryPick:
    """LLM이 고른 것. 스키마 검사를 지났지만 아직 근거 검사 전이다(category-suggestion-rag 7장)."""

    category_id: CategoryId | None
    evidence_ids: tuple[str, ...]
    reason: str
    abstain: bool
    self_confidence: float  # 보관만 한다. 게이팅에는 검색이 계산한 신뢰도를 쓴다(6.3)
