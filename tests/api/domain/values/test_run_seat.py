from __future__ import annotations

from api.domain.values import RunSeat


def test_same_values_as_the_check_constraint():
    assert {s.value for s in RunSeat} == {"capture", "classify", "chat", "ask", "insight", "mcp"}
