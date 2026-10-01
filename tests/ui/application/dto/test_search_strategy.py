from __future__ import annotations

from ui.application.dto import SearchStrategy


def test_cheapest_first():
    assert [s.value for s in SearchStrategy] == ["rule", "history", "vector", "none"]
