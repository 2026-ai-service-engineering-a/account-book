"""문서 — 조각 찾기(docs/ai/document-rag.md).

- `GET /v1/documents/search` — 키워드만. 화면이 api를 바로 부를 때(agent가 없을 때).
- `POST /v1/documents/search` — 키워드·벡터·하이브리드. 벡터는 agent가 임베딩해 본문에 싣는다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from api.application.use_cases.search_documents import DEFAULT_K, MAX_K
from api.domain.values import ChunkStrategy, SearchMode
from api.interfaces.schemas import ChunkHitBody, DocumentSearchRequest
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


@router.post("/search")
def search_by_mode(body: DocumentSearchRequest, services: ServicesDep) -> list[ChunkHitBody]:
    """하이브리드의 점수는 RRF 점수(순위의 역수 합)다 — 키워드·벡터의 0~1 점수와 견주지 않는다."""
    hits = services.search_documents(
        body.q,
        ChunkStrategy(body.strategy),
        body.k,
        SearchMode(body.mode),
        tuple(body.query_vector) if body.query_vector is not None else None,
        body.embedding_model,
    )
    return [ChunkHitBody.of(hit) for hit in hits]
