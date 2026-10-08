from __future__ import annotations

from api.domain.values import SearchMode


def test_three_ways_to_search():
    assert [m.value for m in SearchMode] == ["keyword", "vector", "hybrid"]
