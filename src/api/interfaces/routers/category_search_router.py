"""카테고리 고르기의 검색 — `suggest_category` 도구와 색인(docs/ai/category-suggestion-rag.md).

검색은 api, 판단은 agent다. 여기서는 후보와 근거를 계산해 내려줄 뿐이다. 색인은 agent가 당겨
간다 — api는 agent를 부르지 않는다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.application.use_cases.list_pending_texts import MAX_PENDING
from api.interfaces.schemas import (
    EmbeddingBody,
    PendingBody,
    PendingResponse,
    SuggestRequest,
    SuggestResponse,
)
from api.interfaces.services import ServicesDep
from api.interfaces.write_headers import WriteHeadersDep

router = APIRouter(prefix="/v1")


@router.post("/categories/suggest")
def suggest(body: SuggestRequest, services: ServicesDep) -> SuggestResponse:
    """읽기다 — 확인도 멱등 키도 필요 없다(api-contract 6장)."""
    return SuggestResponse.of(services.suggest(body.query()))


@router.get("/embeddings/pending")
def pending(
    services: ServicesDep,
    model: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=MAX_PENDING)] = 100,
) -> PendingResponse:
    items = services.pending(model, limit)
    return PendingResponse(items=[PendingBody(text_hash=i.text_hash, text=i.text) for i in items])


@router.put("/embeddings/{text_hash}", status_code=204)
def put_embedding(
    text_hash: str, body: EmbeddingBody, services: ServicesDep, headers: WriteHeadersDep
) -> Response:
    """쓰기라 멱등 키가 필요하다. 같은 모델·같은 텍스트면 같은 벡터라 재시도해도 같다."""

    def perform(uow: UnitOfWork) -> StoredReply:
        services.put_embedding(uow, body.model, text_hash, tuple(body.vector))
        return StoredReply(204)

    key_hash = headers.request_hash("PUT", f"/v1/embeddings/{text_hash}", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return Response(status_code=reply.status_code)
