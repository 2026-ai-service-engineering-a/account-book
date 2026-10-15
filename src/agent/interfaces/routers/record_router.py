"""`POST /record` — 채팅의 기록(docs/ai/chat-capture.md). 확인 게이트를 지나야 쓴다.

이벤트는 chat.md 4.1의 것만 쓴다: tool(이름만), proposal(확인 카드), message, error, done.
기록 자리의 글은 코드가 만든다 — token으로 흘리지 않는다(chat-capture 결정 11).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent.application.dto import RecordReply, RunSeat
from agent.application.errors import ModelUnavailable
from agent.application.use_cases.run_records import failed_run
from agent.interfaces.schemas import CaptureRequest
from agent.interfaces.services import Services, ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)

_NO_MODEL = "지금은 AI가 읽지 못해요. 폼으로 넣어 주세요."


@router.post("/record")
async def record(body: CaptureRequest, services: ServicesDep) -> StreamingResponse:
    """한 줄을 읽어 확인 카드를 낸다. 쓰지 않는다 — 제안을 감사 테이블에 남길 뿐이다."""
    return _stream(_proposing(body, services))


@router.post("/record/proposals/{proposal_id}/confirm")
async def confirm(proposal_id: str, services: ServicesDep) -> StreamingResponse:
    """제안 때 정한 멱등 키와 X-Confirmed-By로 쓴다. 두 번 눌러도 한 건이다."""
    return _stream(_replying(services.decide.confirm(proposal_id)))


@router.post("/record/proposals/{proposal_id}/cancel")
async def cancel(proposal_id: str, services: ServicesDep) -> StreamingResponse:
    """취소도 알린다 — 조용히 지우면 기다리는 제안이 남는다(chat.md 5장)."""
    return _stream(_replying(services.decide.cancel(proposal_id)))


async def _proposing(body: CaptureRequest, services: Services) -> AsyncIterator[str]:
    try:
        reply = await services.propose(body.text, body.local_now())
    except ModelUnavailable as error:
        run = failed_run(str(uuid.uuid4()), RunSeat.CAPTURE, body.text, error)
        await services.record(run)
        yield _error("model_unavailable", _NO_MODEL)
        return
    if reply.card is not None:
        yield _sse("tool", "suggest_category")
        yield _sse("tool", "create_transaction")
    async for event in _events(reply):
        yield event


async def _replying(decision: Awaitable[RecordReply]) -> AsyncIterator[str]:
    reply = await decision
    if reply.wrote:
        yield _sse("tool", "create_transaction")
    async for event in _events(reply):
        yield event


async def _events(reply: RecordReply) -> AsyncIterator[str]:
    if reply.code:
        yield _error(reply.code, reply.text)
        return
    if reply.text:
        yield _sse("message", reply.text)
    if reply.card is not None:
        card = reply.card
        proposal = {
            "id": card.proposal_id,
            "occurred_on": card.occurred_on.isoformat(),
            "category_name": card.category_name,
            "direction": card.direction.value,
            "amount": card.amount,
            "account_name": card.account_name,
            "merchant": card.merchant,
            "unsure": list(card.unsure),
        }
        yield _sse("proposal", json.dumps(proposal, ensure_ascii=False))


def _stream(events: AsyncIterator[str]) -> StreamingResponse:
    async def body() -> AsyncIterator[str]:
        try:
            async for event in events:
                yield event
        except Exception:
            # 스트림이 중간에 죽어도 화면이 조용히 멈추지 않게 에러로 끝낸다. 여기서 한 번만 남긴다
            _log.exception("record stream failed")
            yield _error("internal_error", "문제가 생겼어요.")
        yield _sse("done", "")

    return StreamingResponse(
        body(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


def _error(code: str, message: str) -> str:
    return _sse("error", json.dumps({"code": code, "message": message}, ensure_ascii=False))


def _sse(kind: str, data: str) -> str:
    lines = "".join(f"data: {line}\n" for line in data.split("\n"))
    return f"event: {kind}\n{lines}\n"
