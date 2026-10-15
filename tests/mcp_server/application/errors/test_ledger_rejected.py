from __future__ import annotations

from mcp_server.application.errors import LedgerRejected, LedgerUnavailable


def test_is_an_unavailable_ledger_with_a_code():
    error = LedgerRejected(422, "validation_error", {"from": "날짜가 아니다"})
    assert isinstance(error, LedgerUnavailable)
    assert (error.status, error.code, error.details) == (
        422,
        "validation_error",
        {"from": "날짜가 아니다"},
    )
