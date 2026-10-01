from __future__ import annotations

from api.domain.errors import InvalidTransaction


def test_carries_field_details():
    assert InvalidTransaction({"amount": "금액"}).details == {"amount": "금액"}
