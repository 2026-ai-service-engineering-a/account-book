from __future__ import annotations

from mcp_server.application.errors import LedgerUnavailable


def test_is_an_exception():
    assert issubclass(LedgerUnavailable, Exception)
