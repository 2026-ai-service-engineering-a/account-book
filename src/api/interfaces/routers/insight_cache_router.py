"""리포트 AI 영역의 캐시(docs/ai/agentic-reports.md 8장). 도구가 아니다 — agent의 리포트 흐름이
쓴다. 키는 agent가 period · data_version · prompt_version · model로 만든 sha256이다. TTL이 없다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Response

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.interfaces.schemas import InsightCacheBody, InsightCacheWrite
from api.interfaces.services import ServicesDep
from api.interfaces.write_headers import WriteHeadersDep

router = APIRouter(prefix="/v1/insights")

type _Key = Annotated[str, Path(pattern=r"^[0-9a-f]{64}$")]


@router.get("/cache/{key}")
def read(key: _Key, services: ServicesDep) -> InsightCacheBody:
    found = services.read_insight_cache(key)
    return InsightCacheBody(key=key, body=dict(found) if found is not None else None)


@router.put("/cache/{key}", status_code=204)
def put(
    key: _Key, body: InsightCacheWrite, services: ServicesDep, headers: WriteHeadersDep
) -> Response:
    """쓰기라 멱등 키가 필요하다. 같은 키에 다른 답을 쓰면 갈아 끼운다 — 마지막 것이 남는다."""

    def perform(uow: UnitOfWork) -> StoredReply:
        services.put_insight_cache(uow, key, body.body)
        return StoredReply(204)

    key_hash = headers.request_hash("PUT", f"/v1/insights/cache/{key}", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return Response(status_code=reply.status_code)
