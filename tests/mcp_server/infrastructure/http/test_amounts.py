from __future__ import annotations

from mcp_server.infrastructure.http.amounts import amount


def test_an_amount_carries_its_currency_and_none_stays_none():
    assert amount(8500) == {"amount": 8500, "currency": "KRW"}
    assert amount(None) is None
