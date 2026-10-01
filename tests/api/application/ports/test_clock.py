from __future__ import annotations

from datetime import datetime

from api.application.ports import Clock
from tests.api.conftest import SEOUL, FixedClock


def test_fake_fills_the_port():
    port: Clock = FixedClock(datetime(2026, 9, 17, tzinfo=SEOUL))
    assert port is not None
