from __future__ import annotations

from ui.application.values import TextHash


def test_is_a_str_at_runtime():
    assert TextHash("abc") == "abc"
