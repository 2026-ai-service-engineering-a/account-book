from __future__ import annotations

from mcp_server.domain.values import Direction


def test_same_values_as_the_api():
    assert {d.value for d in Direction} == {"expense", "income"}
