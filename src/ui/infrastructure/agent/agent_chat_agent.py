from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import date
from typing import Literal, get_args

import httpx

from ui.application.dto import ChatEvent, Direction, Proposal
from ui.application.dto.chat_event import ChatEventKind
from ui.application.ports import Clock
from ui.application.values import Money, ProposalId

_UNAVAILABLE = "지금은 AI에 닿지 못했어요. 거래 목록에서 직접 볼 수 있어요."
_KINDS = frozenset(get_args(ChatEventKind))
_log = logging.getLogger(__name__)


class AgentChatAgent:
    """AI 자리 ①의 진짜. agent의 SSE를 받아 화면 이벤트로 옮긴다(ui_docs/pages/chat.md 2장).

    `path`가 자리다 — 질문은 `/chat`(query 모드), 기록은 `/record`(확인 게이트). 어느 쪽인지는
    `RoutedChatAgent`가 코드로 정한다. 확인 카드의 답(`decide`)은 언제나 agent의
    `/record/proposals/{id}/confirm|cancel`로 간다 — 확인된 쓰기를 ui가 api로 보내지 않는다
    (chat.md 5.2).

    ui는 해석하지 않는다. 보내고, 이벤트를 그대로 중계한다. agent가 없거나 끊기면 에러 줄로
    끝낸다 — 조용히 멈추지 않는다. 기준 시각과 타임존을 같이 보낸다.
    """

    def __init__(
        self,
        base_url: str,
        timezone: str,
        clock: Clock,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
        path: Literal["/chat", "/record"] = "/chat",
    ) -> None:
        self._path = path
        self._base_url = base_url
        self._timezone = timezone
        self._clock = clock
        self._timeout = timeout  # 이벤트 사이 한 번의 읽기 상한
        self._transport = transport

    async def run(self, utterance: str) -> AsyncIterator[ChatEvent]:
        body = {"text": utterance, "now": self._clock.now().isoformat(), "timezone": self._timezone}
        async for event in self._stream(self._path, body):
            yield event

    async def decide(self, proposal_id: ProposalId, accepted: bool) -> AsyncIterator[ChatEvent]:
        """확인 카드의 답을 agent에 전한다. 취소도 알린다 — 조용히 지우면 제안이 남는다."""
        decision = "confirm" if accepted else "cancel"
        async for event in self._stream(f"/record/proposals/{proposal_id}/{decision}", None):
            yield event

    async def _stream(self, path: str, body: dict[str, str] | None) -> AsyncIterator[ChatEvent]:
        finished = False
        try:
            async with (
                httpx.AsyncClient(
                    base_url=self._base_url, timeout=self._timeout, transport=self._transport
                ) as client,
                client.stream("POST", path, json=body) as response,
            ):
                response.raise_for_status()
                async for event in _events(response.aiter_lines()):
                    finished = finished or event.kind == "done"
                    yield event
        except httpx.HTTPError as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 원문은 남기지 않는다(development-rules 6.4)
            _log.warning("agent chat failed path=%s: %s", path.split("/")[1], type(error).__name__)
            yield ChatEvent("error", _UNAVAILABLE, code="agent_unavailable")
        if not finished:
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
    if kind == "proposal":
        return _proposal(data)
    if kind == "error":
        try:
            body = json.loads(data)
            return ChatEvent("error", str(body["message"]), code=str(body["code"]))
        except (ValueError, KeyError, TypeError):
            return ChatEvent("error", _UNAVAILABLE, code="internal_error")
    return ChatEvent(kind, data)  # type: ignore[arg-type]  # _KINDS로 걸렀다


def _proposal(data: str) -> ChatEvent:
    """확인 카드 한 장. 모양이 틀리면 카드를 그리지 않고 에러로 — 모르는 값을 확인시키지 않는다."""
    try:
        body = json.loads(data)
        proposal = Proposal(
            id=ProposalId(str(body["id"])),
            occurred_on=date.fromisoformat(str(body["occurred_on"])),
            category_name=str(body["category_name"]),
            direction=Direction(str(body["direction"])),
            amount=Money(int(body["amount"])),
            account_name=str(body["account_name"]),
            merchant=str(body.get("merchant", "")),
            unsure=tuple(str(u) for u in body.get("unsure", [])),
        )
    except (ValueError, KeyError, TypeError):
        return ChatEvent("error", _UNAVAILABLE, code="internal_error")
    return ChatEvent("proposal", proposal=proposal)
