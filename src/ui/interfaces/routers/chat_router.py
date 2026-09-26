from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from ui.application.dto import ChatEvent, Period, TransactionFilter
from ui.interfaces.presenters.tool_labels import progress_label
from ui.interfaces.request_id import request_id_of
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import fragment, render

router = APIRouter()
logger = logging.getLogger(__name__)

EXAMPLES = (
    "어제 점심 김밥천국 8500원 카드로",
    "이번 달 식비 얼마 썼어?",
    "이번 달 카페에 얼마 썼어?",
)


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request, services: ServicesDep, q: str = "") -> HTMLResponse:
    period = Period.of(services.clock.now().date())
    totals = await services.reports.totals(TransactionFilter(period))
    context = {"section": "chat", "totals": totals, "period": period, "prefill": q}
    return render(request, "chat.html", context | {"examples": EXAMPLES})


@router.post("/chat")
async def chat_send(
    request: Request, services: ServicesDep, text: Annotated[str, Form()] = ""
) -> StreamingResponse:
    return _stream(request, services.chat.run(text.strip()) if text.strip() else _nothing())


@router.post("/chat/proposals/{proposal_id}/{decision}")
async def chat_decide(
    request: Request,
    services: ServicesDep,
    proposal_id: str,
    decision: Literal["confirm", "cancel"],
) -> StreamingResponse:
    return _stream(request, services.chat.decide(proposal_id, decision == "confirm"))


async def _nothing() -> AsyncIterator[ChatEvent]:
    yield ChatEvent("done")


def _stream(request: Request, events: AsyncIterator[ChatEvent]) -> StreamingResponse:
    request_id = request_id_of(request)

    async def body() -> AsyncIterator[str]:
        try:
            async for event in events:
                yield _encode(event, request_id)
        except Exception:
            # 스트림이 중간에 죽어도 화면이 조용히 멈추지 않게 에러 줄로 끝낸다.
            logger.exception("chat stream failed", extra={"request_id": request_id})
            failure = ChatEvent("error", "문제가 생겼어요.", code="internal_error")
            yield _encode(failure, request_id)
            yield _encode(ChatEvent("done"), request_id)

    return StreamingResponse(
        body(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


def _encode(event: ChatEvent, request_id: str) -> str:
    """SSE 한 덩어리. 화면에 붙일 조각은 서버가 그려 보낸다 — JS는 붙이기만 한다."""
    if event.kind == "tool":
        data = progress_label(event.text)
    elif event.kind == "proposal":
        data = fragment("partials/chat_proposal.html", {"proposal": event.proposal})
    elif event.kind == "message":
        data = fragment("partials/chat_bubble.html", {"text": event.text})
    elif event.kind == "error":
        context = {"message": event.text, "code": event.code, "request_id": request_id}
        data = fragment("partials/chat_error.html", context)
    else:
        data = event.text
    lines = "".join(f"data: {line}\n" for line in data.split("\n"))
    return f"event: {event.kind}\n{lines}\n"
