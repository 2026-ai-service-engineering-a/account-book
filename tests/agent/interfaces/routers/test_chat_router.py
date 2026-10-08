from __future__ import annotations

import json

from agent.application.dto import ModelReply, ModelUsage, ToolCall
from agent.application.errors import LedgerUnavailable
from agent.domain.tools import CategoryLine, Frequency
from agent.domain.values import Amount, CategoryId
from tests.agent.conftest import FakeLedger, FakeModel
from tests.agent.interfaces.conftest import client_with

BODY = {
    "text": "저번 주에 카페 몇 번 갔어?",
    "now": "2026-10-08T09:00:00+09:00",
    "timezone": "Asia/Seoul",
}
DICTIONARY = (CategoryLine(CategoryId("cafe"), "카페"),)
ARGUMENTS = {"period": "last_week", "category_id": "cafe"}


def events(text: str) -> list[tuple[str, str]]:
    """SSE 본문을 (이벤트, 데이터)로. 여러 data 줄은 줄바꿈으로 잇는다."""
    out = []
    for block in text.strip().split("\n\n"):
        lines = block.split("\n")
        kind = lines[0].removeprefix("event: ")
        data = "\n".join(line.removeprefix("data:").removeprefix(" ") for line in lines[1:])
        out.append((kind, data))
    return out


def ledger(**replies: object) -> FakeLedger:
    return FakeLedger(replies={"categories": DICTIONARY, **replies})


def test_tool_then_message_then_done_and_never_the_arguments():
    model = FakeModel(
        tape=[
            ModelReply("", (ToolCall("c1", "count_frequency", ARGUMENTS),), ModelUsage()),
            ModelReply("저번 주에 카페에 3번 갔어요.", (), ModelUsage()),
        ]
    )
    found = ledger(frequency=Frequency(3, 3, 1.0, Amount(5267)))
    response = client_with(model, found).post("/chat", json=BODY)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert events(response.text) == [
        ("tool", "count_frequency"),
        (
            "message",
            "저번 주에 카페에 3번 갔어요.\n\n"
            "저번 주(9/28~10/4) · 카페\n"
            "3번 · 3일 · 평균 1일 간격 · 회당 5,267원",
        ),
        ("done", ""),
    ]
    assert "last_week" not in response.text  # tool 이벤트에 인자를 싣지 않는다


def test_only_events_from_the_chat_page_table():
    model = FakeModel(tape=[ModelReply("예측은 못 해요.", (), ModelUsage())])
    kinds = {k for k, _ in events(client_with(model, ledger()).post("/chat", json=BODY).text)}
    assert kinds <= {"token", "tool", "proposal", "message", "error", "done"}
    assert "token" not in kinds and "proposal" not in kinds


def test_api_down_is_a_message_not_a_crash():
    down = FakeLedger(replies={"categories": LedgerUnavailable("ConnectError")})
    found = events(client_with(FakeModel(), down).post("/chat", json=BODY).text)
    assert found[0][0] == "message" and "지금은 답할 수 없어요" in found[0][1]
    assert found[-1] == ("done", "")


def test_unexpected_failures_end_with_an_error_and_done():
    class Broken(FakeLedger):
        async def categories(self) -> tuple[CategoryLine, ...]:
            raise RuntimeError("boom")

    found = events(client_with(FakeModel(), Broken()).post("/chat", json=BODY).text)
    assert found[0][0] == "error" and json.loads(found[0][1])["code"] == "internal_error"
    assert found[-1] == ("done", "")


def test_a_bad_body_is_422_before_the_stream():
    assert client_with(FakeModel()).post("/chat", json={"text": "q"}).status_code == 422
