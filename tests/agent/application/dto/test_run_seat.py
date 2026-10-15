from __future__ import annotations

from agent.application.dto import RunSeat


def test_same_values_as_the_api_check():
    assert {s.value for s in RunSeat} == {"capture", "classify", "chat", "ask"}


def test_only_chat_is_react():
    assert {s.flow for s in RunSeat if s is not RunSeat.CHAT} == {"single"}
    assert RunSeat.CHAT.flow == "react"
