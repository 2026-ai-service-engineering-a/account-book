from __future__ import annotations

from agent.application.errors import LedgerUnavailable, ModelUnavailable


def test_is_not_a_model_problem():
    assert not issubclass(LedgerUnavailable, ModelUnavailable)
