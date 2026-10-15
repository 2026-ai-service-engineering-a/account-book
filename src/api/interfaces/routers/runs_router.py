"""감사 로그 — agent가 실행 하나와 그 도구 호출들을 남긴다(docs/ai/README.md 2장 원칙 7).

도구가 아니다. 모델이 고르는 길이 없고, agent의 자리가 끝날 때 코드가 부른다.
쓰기 제안은 `awaiting_confirmation`으로 넣고 확인(`/confirm`)·닫기(`/close`)로 이어진다
(docs/ai/chat-capture.md).
둘 다 "지금 대기일 때만" 바꾸고 결정 뒤의 실행을 돌려준다.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.domain.values import RunStatus
from api.interfaces.schemas import RunBody, RunDecision, RunWrite
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


@router.get("/runs/{run_id}")
def read_run(run_id: str, services: ServicesDep) -> RunBody:
    return RunBody.of(services.read_run(run_id))


@router.post("/runs/{run_id}/confirm")
def confirm_run(
    run_id: str, body: RunDecision, services: ServicesDep, headers: WriteHeadersDep
) -> JSONResponse:
    """그 호출의 confirmed_at을 비어 있을 때만 채운다. 두 번 눌러도 처음 시각이 남는다."""

    def perform(uow: UnitOfWork) -> StoredReply:
        found = services.decide_run.confirm(uow, run_id, body.call_id)
        return StoredReply(200, RunBody.of(found).model_dump(mode="json"))

    key_hash = headers.request_hash("POST", f"/v1/runs/{run_id}/confirm", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return JSONResponse(dict(reply.body or {}), status_code=reply.status_code)


@router.post("/runs/{run_id}/close")
def close_run(
    run_id: str, body: RunDecision, services: ServicesDep, headers: WriteHeadersDep
) -> JSONResponse:
    """대기인 제안을 done·aborted로 닫는다. 확인된 제안은 aborted로 닫히지 않는다."""
    status = RunStatus(body.status) if body.status else RunStatus.DONE

    def perform(uow: UnitOfWork) -> StoredReply:
        found = services.decide_run.close(
            uow, run_id, status, body.stop_reason or status.value, body.result_map()
        )
        return StoredReply(200, RunBody.of(found).model_dump(mode="json"))

    key_hash = headers.request_hash("POST", f"/v1/runs/{run_id}/close", body)
    reply = services.write(headers.idempotency_key, key_hash, perform)
    return JSONResponse(dict(reply.body or {}), status_code=reply.status_code)
