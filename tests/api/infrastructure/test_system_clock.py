from __future__ import annotations

from zoneinfo import ZoneInfo

from api.application.ports import Clock
from api.infrastructure.system_clock import SystemClock


def test_aware_in_the_users_zone():
    port: Clock = SystemClock(ZoneInfo("Asia/Seoul"))
    now = port.now()
    assert now.tzinfo is not None and now.utcoffset().total_seconds() == 9 * 3600  # type: ignore[union-attr]
