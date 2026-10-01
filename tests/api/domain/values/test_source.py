from __future__ import annotations

from api.domain.values import Source


def test_same_values_as_the_check_constraint():
    assert {s.value for s in Source} == {"manual", "agent", "import"}
