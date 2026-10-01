from __future__ import annotations

import asyncio

import httpx
import pytest

from tests.ui.infrastructure.api.conftest import client, recorder
from ui.application.errors import LedgerUnavailable, LedgerValidationError, TransactionNotFound


def call(status: int, body: object):
    handler, _ = recorder(status, body)
    return asyncio.run(client(handler).request("GET", "/v1/x"))


def test_success_passes_through():
    assert call(200, {"ok": True}).json() == {"ok": True}


def test_error_codes_become_ui_errors():
    with pytest.raises(TransactionNotFound):
        call(404, {"error": {"code": "not_found", "message": "m"}})
    with pytest.raises(LedgerValidationError) as caught:
        call(
            422,
            {"error": {"code": "validation_error", "message": "m", "details": {"amount": "금액"}}},
        )
    assert caught.value.details == {"amount": "금액"}


@pytest.mark.parametrize(
    ("status", "body"),
    [(503, {"error": {"code": "db_unavailable"}}), (500, "not json"), (412, {"error": {}})],
)
def test_everything_else_is_unavailable(status, body):
    with pytest.raises(LedgerUnavailable):
        call(status, body)


def test_connection_failure_is_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(LedgerUnavailable, match="ConnectError"):
        asyncio.run(client(handler).request("GET", "/v1/x"))
