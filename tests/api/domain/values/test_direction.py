from __future__ import annotations

from api.domain.values import Direction


def test_same_values_as_the_check_constraint():
    assert {d.value for d in Direction} == {"expense", "income"}
