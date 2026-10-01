from __future__ import annotations

from api.interfaces.missing_idempotency_key import MissingIdempotencyKey


def test_is_an_exception():
    assert issubclass(MissingIdempotencyKey, Exception)
