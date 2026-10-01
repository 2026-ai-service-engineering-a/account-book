from __future__ import annotations

from dataclasses import dataclass

from api.domain.entities import Category

from .category_candidate import CategoryCandidate
from .category_evidence import CategoryEvidence
from .search_strategy import SearchStrategy


@dataclass(frozen=True, slots=True)
class CategorySearch:
    """`POST /v1/categories/suggest`의 답. 후보·근거와 함께 그 방향의 카테고리 사전을 낸다.

    사전을 같이 내는 것은 도구 하나가 엔드포인트 하나를 부르게 하려는 것이다
    (docs/api-contract.md 6장). LLM은 이 사전 밖의 값을 고를 수 없다.
    """

    strategy: SearchStrategy
    query_text: str  # 정규화한 색인 텍스트. agent는 이걸 임베딩한다
    needs_query_vector: bool  # 벡터가 있으면 더 찾을 수 있다 — agent가 계산해 다시 부른다
    candidates: tuple[CategoryCandidate, ...]
    evidence: tuple[CategoryEvidence, ...]
    categories: tuple[Category, ...]
