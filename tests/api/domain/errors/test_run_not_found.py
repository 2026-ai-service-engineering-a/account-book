from __future__ import annotations

from api.domain.errors import RunNotFound


def test_carries_the_code():
    assert str(RunNotFound()) == "not_found"
