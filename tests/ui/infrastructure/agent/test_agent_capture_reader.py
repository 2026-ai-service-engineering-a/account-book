from __future__ import annotations

import asyncio
import json
from datetime import datetime

import httpx

from tests.ui.conftest import NOW, SEOUL
from ui.application.dto import Direction, MessageReading
from ui.application.ports import CaptureReader
from ui.application.values import AccountId, Money
from ui.infrastructure.agent import AgentCaptureReader

READ = {
    "direction": "expense",
    "amount": 5000,
    "occurred_at": "2026-09-17T15:00:00+09:00",
    "payment_method": None,
    "merchant": "카페",
    "refusal": "",
}


def reader(handler) -> AgentCaptureReader:
    return AgentCaptureReader(
        "http://agent", "Asia/Seoul", timeout=1, transport=httpx.MockTransport(handler)
    )


def read(handler, text: str = "오늘 오후 3시에 카페에서 5천원 썼어") -> MessageReading:
    return asyncio.run(reader(handler).read(text, NOW))


def answer(status: int = 200, body: object = READ):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body)

    return handler


def test_fills_the_port():
    port: CaptureReader = reader(answer())
    assert port is not None


def test_sends_text_reference_time_and_zone():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=READ)

    read(handler, "카페 5천원")
    assert seen[0].url == "http://agent/capture"
    assert json.loads(seen[0].content) == {
        "text": "카페 5천원",
        "now": NOW.isoformat(),
        "timezone": "Asia/Seoul",
    }


def test_reading_becomes_ui_values():
    reading = read(answer(body=READ | {"payment_method": "card"}))
    assert reading == MessageReading(
        direction=Direction.EXPENSE,
        amount=Money(5000),
        occurred_at=datetime(2026, 9, 17, 15, tzinfo=SEOUL),
        account_id=AccountId("card"),
        merchant="카페",
    )


def test_agents_refusal_is_passed_on():
    body = {k: None for k in READ} | {"refusal": "질문은 채팅에서 물어 주세요."}
    assert read(answer(body=body)) == MessageReading(refusal="질문은 채팅에서 물어 주세요.")


def test_agent_down_is_a_refusal_not_a_crash():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    reading = read(handler)
    assert reading.amount is None and "직접 채워" in reading.refusal


def test_model_unavailable_is_a_refusal():
    body = {"error": {"code": "model_unavailable", "message": "x"}}
    assert read(answer(503, body)).refusal


def test_strange_answer_is_a_refusal():
    # 바깥에서 온 JSON이다. 모양이 다르면 칸을 채우지 않는다
    assert read(answer(body=READ | {"amount": -5})).refusal
    assert read(answer(body=READ | {"occurred_at": "2026-09-17T15:00:00"})).refusal
