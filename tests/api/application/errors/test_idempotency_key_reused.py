from __future__ import annotations

from api.application.errors import IdempotencyKeyReused


def test_is_an_exception():
    assert issubclass(IdempotencyKeyReused, Exception)
