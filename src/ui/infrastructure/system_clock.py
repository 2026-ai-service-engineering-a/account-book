from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


class SystemClock:
    def __init__(self, zone: ZoneInfo) -> None:
        self._zone = zone

    def now(self) -> datetime:
        return datetime.now(self._zone)
