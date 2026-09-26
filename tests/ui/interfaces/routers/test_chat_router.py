from __future__ import annotations

from tests.ui.interfaces.conftest import extract, sse_events


def test_first_visit_shows_examples(empty_client):
    page = empty_client.get("/?q=식비 왜 늘었어?")
    assert page.status_code == 200
    assert "이렇게 말해보세요" in page.text
    assert "식비 왜 늘었어?</textarea>" in page.text


def test_record_through_confirmation_card(empty_client):
    stream = empty_client.post("/chat", data={"text": "어제 점심 김밥천국 8500원 카드로"})
    assert stream.headers["content-type"].startswith("text/event-stream")
    events = sse_events(stream.text)
    assert [name for name, _ in events] == ["tool", "tool", "proposal", "done"]
    assert events[0][1] == "카테고리를 고르는 중…"
    card = events[2][1]
    assert "2026-09-16 · 식비 ·" in card and "-8,500원" in card
    proposal_id = extract(r'data-proposal-id="(\w+)"', card)

    result = sse_events(empty_client.post(f"/chat/proposals/{proposal_id}/confirm").text)
    assert result[-2][0] == "message" and "기록했어요." in result[-2][1]

    listing = empty_client.get("/transactions?period=2026-09")
    assert "김밥천국" in listing.text and "에이전트가 넣은 기록" in listing.text


def test_decision_twice_is_an_error_line(empty_client):
    card = sse_events(empty_client.post("/chat", data={"text": "스타벅스 5800원"}).text)[2][1]
    proposal_id = extract(r'data-proposal-id="(\w+)"', card)
    empty_client.post(f"/chat/proposals/{proposal_id}/cancel")
    again = sse_events(empty_client.post(f"/chat/proposals/{proposal_id}/confirm").text)
    assert again[0][0] == "error" and "요청 id" in again[0][1]


def test_blank_message_just_finishes(empty_client):
    assert sse_events(empty_client.post("/chat", data={"text": "  "}).text) == [("done", "")]


def test_unknown_decision_is_rejected(empty_client):
    assert empty_client.post("/chat/proposals/x/maybe").status_code == 422
