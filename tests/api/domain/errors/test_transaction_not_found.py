from __future__ import annotations

from api.domain.errors import TransactionNotFound


def test_is_an_exception():
    assert issubclass(TransactionNotFound, Exception)
