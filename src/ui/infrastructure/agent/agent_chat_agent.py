from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import get_args

import httpx

from ui.application.dto import ChatEvent
from ui.application.dto.chat_event import ChatEventKind
from ui.application.ports import Clock
from ui.application.values import ProposalId

_UNAVAILABLE = "지금은 AI에 닿지 못했어요. 거래 목록에서 직접 볼 수 있어요."
_KINDS = frozenset(get_args(ChatEventKind))
_log = logging.getLogger(__name__)


class AgentChatAgent:
    """AI 자리 ①의 질문 쪽 진짜. agent의 `POST /chat` SSE를 받아 화면 이벤트로 옮긴다.

    ui는 질문을 해석하지 않는다. 보내고, 이벤트를 그대로 중계한다(ui_docs/pages/chat.md 2장).
    agent가 없거나 끊기면 에러 줄로 끝낸다 — 조용히 멈추지 않는다. 기준 시각과 타임존을
    같이 보낸다 — "저번 주"는 사용자 타임존의 오늘로 푼다.
    """

    def __init__(
        self,
        base_url: str,
        timezone: str,
        clock: Clock,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timezone = timezone
        self._clock = clock
        self._timeout = timeout  # 이벤트 사이 한 번의 읽기 상한
        self._transport = transport

    async def run(self, utterance: str) -> AsyncIterator[ChatEvent]:
        body = {"text": utterance, "now": self._clock.now().isoformat(), "timezone": self._timezone}
        finished = False
        try:
            async with (
                httpx.AsyncClient(
                    base_url=self._base_url, timeout=self._timeout, transport=self._transport
                ) as client,
                client.stream("POST", "/chat", json=body) as response,
            ):
                response.raise_for_status()
                async for event in _events(response.aiter_lines()):
                    finished = finished or event.kind == "done"
                    yield event
        except httpx.HTTPError as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 질문 원문은 남기지 않는다(development-rules 6.4)
            _log.warning("agent chat failed: %s", type(error).__name__)
            yield ChatEvent("error", _UNAVAILABLE, code="agent_unavailable")
        if not finished:
            yield ChatEvent("done")

    async def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        """질문 쪽은 쓰기를 제안하지 않는다. 받은 확인은 엉뚱한 곳에서 온 것이다."""
        yield ChatEvent("error", "그 제안을 찾지 못했어요.", code="not_found")
        yield ChatEvent("done")


async def _events(lines: AsyncIterator[str]) -> AsyncIterator[ChatEvent]:
    """SSE 줄을 이벤트로. 빈 줄이 이벤트 하나의 끝이고, data 여러 줄은 줄바꿈으로 잇는다."""
    kind, data = "", []
    async for line in lines:
        if line.startswith("event:"):
            kind = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data.append(line.removeprefix("data:").removeprefix(" "))
        elif not line and kind:
            event = _event(kind, "\n".join(data))
            if event is not None:
                yield event
            kind, data = "", []


def _event(kind: str, data: str) -> ChatEvent | None:
    if kind not in _KINDS:
        return None  # 모르는 이벤트는 그리지 않는다 — 이벤트 표는 chat.md 4.1이 정본이다
    if kind == "error":
        try:
            body = json.loads(data)
            return ChatEvent("error", str(body["message"]), code=str(body["code"]))
        except (ValueError, KeyError, TypeError):
            return ChatEvent("error", _UNAVAILABLE, code="internal_error")
    return ChatEvent(kind, data)  # type: ignore[arg-type]  # _KINDS로 걸렀다
