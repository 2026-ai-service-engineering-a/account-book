from __future__ import annotations

from agent.application.dto import PendingText


def test_hash_and_text():
    assert PendingText("h", "스타벅스").text == "스타벅스"
