from __future__ import annotations

from agent.domain.tools import Permission


def test_one_read_and_two_kinds_of_write():
    assert [p.value for p in Permission] == ["read", "write_confirm", "write_always_confirm"]
