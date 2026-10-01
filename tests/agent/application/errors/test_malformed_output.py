from __future__ import annotations

from agent.application.errors import MalformedOutput, ModelUnavailable


def test_is_not_unavailability():
    # 둘은 다르게 다룬다 — 틀린 모양은 다시 시키고, 닿지 못한 건 다시 시키지 않는다
    assert not issubclass(MalformedOutput, ModelUnavailable)
