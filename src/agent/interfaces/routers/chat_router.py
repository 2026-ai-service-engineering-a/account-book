"""`POST /chat` — 대화로 묻는 통계의 SSE(ui_docs/pages/chat.md 4.1).

이벤트는 chat.md 4.1의 것만 쓴다: tool(도구 이름만), message(완결된 답), error, done.
token은 내지 않는다 — 답의 숫자를 검증한 뒤에야 문장을 내보낼 수 있다(chat-analytics 7.2).
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent.application.use_cases.answer_text import answer_text
from agent.interfaces.schemas import ChatRequest
from agent.interfaces.services import Services, ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/chat")
async def chat(body: ChatRequest, services: ServicesDep) -> StreamingResponse:
    """질문 하나를 query 모드로 답한다. 쓰기 도구가 없어 기록이 바뀌는 길이 없다."""
    return StreamingResponse(
        _events(body, services),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


async def _events(body: ChatRequest, services: Services) -> AsyncIterator[str]:
    today = body.local_now().date()  # 사용자 타임존의 오늘 — 기간 이름을 푸는 기준
    try:
        async for event in services.answer(body.text, today, ZoneInfo(body.timezone)):
            if event.outcome is None:
                yield _sse("tool", event.tool)  # 이름만. 인자는 싣지 않는다
            else:
                yield _sse("message", answer_text(event.outcome, today))
    except Exception:
        # 스트림이 중간에 죽어도 화면이 조용히 멈추지 않게 에러로 끝낸다. 여기서 한 번만 남긴다
        _log.exception("chat stream failed")
        error = {"code": "internal_error", "message": "문제가 생겼어요."}
        yield _sse("error", json.dumps(error, ensure_ascii=False))
    yield _sse("done", "")


def _sse(kind: str, data: str) -> str:
    lines = "".join(f"data: {line}\n" for line in data.split("\n"))
    return f"event: {kind}\n{lines}\n"
