from __future__ import annotations

from tests.ui.conftest import SEOUL
from ui.infrastructure.system_clock import SystemClock


def test_now_is_aware_in_user_zone():
    now = SystemClock(SEOUL).now()
    assert now.tzinfo is SEOUL
