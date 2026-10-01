from __future__ import annotations

from agent.domain.values import CategoryId


def test_is_a_str_at_runtime():
    assert CategoryId("cafe") == "cafe"
