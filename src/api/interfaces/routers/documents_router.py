"""문서 — `GET /v1/documents/search`(키워드 검색). 화면이 부른다(docs/ai/document-rag.md).

지금은 pg_trgm의 키워드 검색 하나다. 벡터 검색은 doc-index에서 붙는다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from api.application.use_cases.search_documents import DEFAULT_K, MAX_K
from api.domain.values import ChunkStrategy
from api.interfaces.schemas import ChunkHitBody
from api.interfaces.services import ServicesDep

router = APIRouter(prefix="/v1/documents")


@router.get("/search")
def search(
    services: ServicesDep,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    k: Annotated[int, Query(ge=1, le=MAX_K)] = DEFAULT_K,
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"] = "paragraph",
) -> list[ChunkHitBody]:
    """한 전략의 조각 중 키워드가 가장 비슷한 k개, 점수 높은 순. 점수로 거르지 않는다."""
    hits = services.search_documents(q, ChunkStrategy(strategy), k)
    return [ChunkHitBody.of(hit) for hit in hits]
