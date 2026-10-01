from __future__ import annotations

from api.domain.values import TransactionId


def test_is_a_str_at_runtime():
    assert TransactionId("t1") == "t1"
