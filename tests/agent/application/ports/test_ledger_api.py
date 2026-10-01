from __future__ import annotations

import inspect

from agent.application.ports import LedgerApi
from agent.infrastructure.http import HttpLedgerApi
from tests.agent.conftest import FakeLedger


def test_http_client_and_fake_fill_the_port():
    real: LedgerApi = HttpLedgerApi("http://api", timeout=1)
    fake: LedgerApi = FakeLedger()
    assert inspect.iscoroutinefunction(real.suggest)
    assert inspect.iscoroutinefunction(fake.put_embedding)
