from __future__ import annotations

import inspect

from mcp_server.application.ports import LedgerApi
from mcp_server.infrastructure.http import HttpLedgerApi
from tests.mcp_server.conftest import FakeLedger


def test_http_client_and_fake_fill_the_port():
    real: LedgerApi = HttpLedgerApi("http://api", timeout=1)
    fake: LedgerApi = FakeLedger()
    assert inspect.iscoroutinefunction(real.budget_status)
    assert inspect.iscoroutinefunction(fake.compare)
