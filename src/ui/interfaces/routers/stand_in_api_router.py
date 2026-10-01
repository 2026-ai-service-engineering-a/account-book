"""api 대역의 HTTP 입구 — 카테고리 검색과 색인. agent만 부른다(docs/api-contract.md 6장).

ui의 다른 라우터와 달리 화면이 없고 JSON만 말한다. 대역 기간에는 ui의 공개 포트에 같이
열린다는 한계가 있다(ui_docs/stand-ins.md 3장).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse

from ui.application.ports import CategoryIndex
from ui.application.values import TextHash
from ui.interfaces.services import ServicesDep
from ui.interfaces.stand_in_api import (
    EmbeddingBody,
    PendingBody,
    PendingResponse,
    SuggestRequest,
    SuggestResponse,
)

router = APIRouter(prefix="/v1")
_PENDING_LIMIT = 200


@router.post("/categories/suggest")
async def suggest(body: SuggestRequest, services: ServicesDep) -> SuggestResponse:
    return SuggestResponse.of(await _index(services.index).suggest(body.query()))


@router.get("/embeddings/pending")
async def pending(
    services: ServicesDep,
    model: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=_PENDING_LIMIT)] = 100,
) -> PendingResponse:
    items = await _index(services.index).pending(model, limit)
    return PendingResponse(items=[PendingBody(text_hash=i.text_hash, text=i.text) for i in items])


@router.put("/embeddings/{text_hash}", status_code=204)
async def put_embedding(
    text_hash: str,
    body: EmbeddingBody,
    services: ServicesDep,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> Response:
    # 쓰기에는 키가 필수다(docs/api-contract.md 3장). PUT은 원래 멱등이라 같은 키·같은 본문이
    # 다시 와도 같은 결과다. 대역은 키를 저장하지 않고 있는지만 본다.
    if not idempotency_key:
        error = {"code": "idempotency_key_required", "message": "Idempotency-Key가 필요합니다."}
        return JSONResponse({"error": error}, status_code=400)
    await _index(services.index).put_embedding(TextHash(text_hash), body.model, tuple(body.vector))
    return Response(status_code=204)


def _index(index: CategoryIndex | None) -> CategoryIndex:
    if index is None:  # 조립하지 않았으면 라우터도 붙지 않는다(web_app). 여기 오면 조립이 틀렸다
        raise RuntimeError("CategoryIndex가 조립되지 않았다")
    return index
