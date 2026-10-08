from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId


@dataclass(frozen=True, slots=True)
class CategoryLine:
    """카테고리 사전의 한 줄. 모델은 이 목록 밖의 값을 고를 수 없다."""

    id: CategoryId
    name: str
