from __future__ import annotations

import pytest

from api.interfaces.missing_idempotency_key import MissingIdempotencyKey
from api.interfaces.schemas import TransactionWrite
from api.interfaces.write_headers import WriteHeaders, read_write_headers

BODY = {
    "direction": "expense",
    "amount": 8500,
    "occurred_at": "2026-09-16T12:30:00+09:00",
    "category_id": "food",
    "account_id": "card",
}


def test_key_is_required():
    with pytest.raises(MissingIdempotencyKey):
        read_write_headers(None, None, None)


def test_only_user_counts_as_a_confirmation():
    assert read_write_headers("k", "user", None).confirmed
    assert not read_write_headers("k", "agent", None).confirmed


def test_same_body_same_hash_whatever_the_key_order():
    headers = WriteHeaders("k", True, None)
    one = TransactionWrite.model_validate(BODY)
    two = TransactionWrite.model_validate(dict(reversed(list(BODY.items()))))
    assert headers.request_hash("POST", "/x", one) == headers.request_hash("POST", "/x", two)
    other = TransactionWrite.model_validate(BODY | {"amount": 9000})
    assert headers.request_hash("POST", "/x", one) != headers.request_hash("POST", "/x", other)
