from __future__ import annotations

from agent.application.dto import SearchStrategy


def test_same_four_as_the_api():
    assert [s.value for s in SearchStrategy] == ["rule", "history", "vector", "none"]
