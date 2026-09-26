from __future__ import annotations

from ui.application.dto import ChatEvent


def test_tool_event_carries_only_the_tool_name():
    # chat.md 4.1: tool 이벤트에 도구 인자를 싣지 않는다
    event = ChatEvent("tool", "search_transactions")
    assert (event.kind, event.text, event.proposal, event.code) == (
        "tool",
        "search_transactions",
        None,
        "",
    )


def test_done_has_nothing():
    assert ChatEvent("done") == ChatEvent("done", "", None, "")
