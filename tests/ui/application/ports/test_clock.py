from __future__ import annotations

from tests.ui.conftest import SEOUL, FixedClock
from ui.application.ports import Clock
from ui.infrastructure.system_clock import SystemClock


def test_both_clocks_fill_the_port():
    # 시계는 aware 시각만 낸다(development-rules 6.1)
    clocks: list[Clock] = [SystemClock(SEOUL), FixedClock()]
    assert all(clock.now().tzinfo is not None for clock in clocks)
