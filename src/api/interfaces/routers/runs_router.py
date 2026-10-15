"""감사 로그 — agent가 끝난 실행 하나와 그 도구 호출들을 남긴다(docs/ai/README.md 2장 원칙 7).

도구가 아니다. 모델이 고르는 길이 없고, agent의 자리(capture·classify·chat·ask)가 끝날 때
코드가 부른다. 읽는 길은 감사 화면(feature/audit-page)에서 붙인다.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.interfaces.schemas import RunWrite
from api.interfaces.services import ServicesDep
from api.interfaces.write_headers import WriteHeadersDep

router = APIRouter(prefix="/v1")


@router.post("/runs", status_code=201)
def record_run(body: RunWrite, services: ServicesDep, headers: WriteHeadersDep) -> JSONResponse:
    """쓰기라 멱등 키가 필요하다. agent는 `run:{run_id}`로 보낸다 — 다시 보내도 한 줄이다."""

    def perform(uow: UnitOfWork) -> StoredReply:
        services.record_run(uow, body.record())
        return StoredReply(201, {"id": body.id})

    key_hash = headers.request_hash("POST", "/v1/runs", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return JSONResponse(dict(reply.body or {}), status_code=reply.status_code)
