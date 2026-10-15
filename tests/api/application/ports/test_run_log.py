from __future__ import annotations

from api.application.ports import RunLog
from tests.api.fake_runs import FakeRuns


def test_fake_fills_the_port():
    port: RunLog = FakeRuns()
    assert port is not None
