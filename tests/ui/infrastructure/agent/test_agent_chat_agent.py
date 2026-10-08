from __future__ import annotations

import asyncio
import json

import httpx

from tests.ui.conftest import FixedClock
from ui.application.dto import ChatEvent
from ui.application.ports import ChatAgent
from ui.application.values import ProposalId
from ui.infrastructure.agent import AgentChatAgent

STREAM = (
    "event: tool\ndata: count_frequency\n\n"
    "event: message\ndata: 저번 주에 카페에 3번 갔어요.\ndata: \n"
    "data: 저번 주(9/28~10/4) · 카페\n\n"
    "event: done\ndata: \n\n"
)


def agent(handler) -> AgentChatAgent:
    return AgentChatAgent(
        "http://agent",
        "Asia/Seoul",
        FixedClock(),
        timeout=1,
        transport=httpx.MockTransport(handler),
    )


def stream(body: str, seen: list[httpx.Request] | None = None, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, text=body, headers={"content-type": "text/event-stream"})

    return handler


def collect(chat: ChatAgent, utterance: str = "저번 주에 카페 몇 번 갔어?") -> list[ChatEvent]:
    async def go() -> list[ChatEvent]:
        return [e async for e in chat.run(utterance)]

    return asyncio.run(go())


def test_relays_the_agents_events_with_the_users_reference_time():
    seen: list[httpx.Request] = []
    events = collect(agent(stream(STREAM, seen)))
    assert [e.kind for e in events] == ["tool", "message", "done"]
    assert events[0].text == "count_frequency"
    assert events[1].text == "저번 주에 카페에 3번 갔어요.\n\n저번 주(9/28~10/4) · 카페"
    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/chat" and body["timezone"] == "Asia/Seoul"
    assert body["now"] == "2026-09-17T18:00:00+09:00"


def test_error_events_keep_their_code():
    error = json.dumps(
        {"code": "internal_error", "message": "문제가 생겼어요."}, ensure_ascii=False
    )
    body = f"event: error\ndata: {error}\n\nevent: done\ndata: \n\n"
    events = collect(agent(stream(body)))
    assert (events[0].kind, events[0].code, events[0].text) == (
        "error",
        "internal_error",
        "문제가 생겼어요.",
    )


def test_unknown_events_are_not_drawn_and_a_missing_done_is_added():
    events = collect(agent(stream("event: thought\ndata: 음…\n\nevent: tool\ndata: x\n\n")))
    assert [e.kind for e in events] == ["tool", "done"]


def test_an_unreachable_or_failing_agent_ends_with_an_error_line():
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    for handler in (refused, stream("", status=503)):
        events = collect(agent(handler))
        assert [e.kind for e in events] == ["error", "done"]
        assert events[0].code == "agent_unavailable"


def test_the_question_side_never_has_a_proposal_to_confirm():
    async def go() -> list[ChatEvent]:
        return [e async for e in agent(stream(STREAM)).decide(ProposalId("p1"), True)]

    events = asyncio.run(go())
    assert [(e.kind, e.code) for e in events] == [("error", "not_found"), ("done", "")]
