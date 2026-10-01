from __future__ import annotations

from datetime import datetime, tzinfo


class SystemClock:
    """진짜 시계. `datetime.now`를 부르는 유일한 자리다 — 나머지는 Clock 포트만 안다(6.1)."""

    def __init__(self, zone: tzinfo) -> None:
        self._zone = zone

    def now(self) -> datetime:
        return datetime.now(self._zone)
