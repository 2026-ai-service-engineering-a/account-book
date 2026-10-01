from __future__ import annotations

from api.application.dto import IndexText


def test_hash_and_text():
    assert IndexText("h", "스타벅스").text == "스타벅스"
