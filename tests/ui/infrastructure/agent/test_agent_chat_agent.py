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


CARD = {
    "id": "run-1",
    "occurred_on": "2026-10-14",
    "category_name": "기타",
    "direction": "expense",
    "amount": 8500,
    "account_name": "카드",
    "merchant": "김밥천국",
    "unsure": ["category"],
}
RECORD = (
    "event: tool\ndata: suggest_category\n\n"
    "event: tool\ndata: create_transaction\n\n"
    f"event: proposal\ndata: {json.dumps(CARD, ensure_ascii=False)}\n\n"
    "event: done\ndata: \n\n"
)


def recorder(handler) -> AgentChatAgent:
    return AgentChatAgent(
        "http://agent", "Asia/Seoul", FixedClock(), timeout=1,
        transport=httpx.MockTransport(handler), path="/record",
    )  # fmt: skip


def test_a_record_goes_to_the_record_seat_and_comes_back_as_a_card():
    seen: list[httpx.Request] = []
    events = collect(recorder(stream(RECORD, seen)), "어제 점심 김밥천국 8500원")
    assert seen[0].url.path == "/record"
    assert [e.kind for e in events] == ["tool", "tool", "proposal", "done"]
    card = events[2].proposal
    assert card is not None and card.id == "run-1" and card.amount.amount == 8500
    assert card.unsure == ("category",)


def test_a_card_of_an_unknown_shape_is_not_drawn():
    broken = 'event: proposal\ndata: {"id": "run-1"}\n\nevent: done\ndata: \n\n'
    events = collect(recorder(stream(broken)), "8500원")
    assert [(e.kind, e.code) for e in events] == [("error", "internal_error"), ("done", "")]


def test_confirm_and_cancel_go_to_the_agent_not_the_api():
    seen: list[httpx.Request] = []
    done = "event: message\ndata: 기록했어요.\n\nevent: done\ndata: \n\n"

    async def go(accepted: bool) -> list[ChatEvent]:
        side = agent(stream(done, seen))  # 질문 쪽 인스턴스여도 확인은 기록 자리로 간다
        return [e async for e in side.decide(ProposalId("run-1"), accepted)]

    assert [e.kind for e in asyncio.run(go(True))] == ["message", "done"]
    asyncio.run(go(False))
    assert [r.url.path for r in seen] == [
        "/record/proposals/run-1/confirm",
        "/record/proposals/run-1/cancel",
    ]
