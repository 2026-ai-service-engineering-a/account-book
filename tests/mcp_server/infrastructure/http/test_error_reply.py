from __future__ import annotations

import httpx

from mcp_server.application.errors import LedgerRejected
from mcp_server.infrastructure.http.error_reply import ErrorReply


def test_reads_the_code_and_details():
    response = httpx.Response(
        422, json={"error": {"code": "validation_error", "message": "x", "details": {"to": "날짜"}}}
    )
    error = ErrorReply.rejection(response)
    assert isinstance(error, LedgerRejected) and error.details == {"to": "날짜"}


def test_an_unknown_4xx_is_a_breakage_not_a_refusal():
    error = ErrorReply.rejection(httpx.Response(418, text="teapot"))
    assert not isinstance(error, LedgerRejected)
