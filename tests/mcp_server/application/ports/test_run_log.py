from __future__ import annotations

import inspect

from mcp_server.application.ports import RunLog
from mcp_server.infrastructure.http import HttpRunLog
from tests.mcp_server.conftest import FakeRunLog


def test_http_client_and_fake_fill_the_port():
    real: RunLog = HttpRunLog("http://api", timeout=1)
    fake: RunLog = FakeRunLog()
    assert inspect.iscoroutinefunction(real.record)
    assert inspect.iscoroutinefunction(fake.record)
