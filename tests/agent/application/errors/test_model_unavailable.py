from __future__ import annotations

from agent.application.errors import ModelUnavailable


def test_is_an_exception():
    assert issubclass(ModelUnavailable, Exception)
