from __future__ import annotations

from agent.domain.values import Direction


def test_values_match_the_wire():
    assert [d.value for d in Direction] == ["expense", "income"]
