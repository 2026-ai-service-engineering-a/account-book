from __future__ import annotations

import inspect

from agent.application.ports import RunRecorder
from agent.infrastructure.http import HttpRunRecorder
from tests.agent.conftest import FakeRecorder


def test_adapter_and_fake_fill_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    real: RunRecorder = HttpRunRecorder("http://api:8000", timeout=1)
    fake: RunRecorder = FakeRecorder()
    assert inspect.iscoroutinefunction(real.record)
    assert inspect.iscoroutinefunction(fake.record)
