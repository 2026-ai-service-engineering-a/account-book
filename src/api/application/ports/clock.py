from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """지금. `datetime.now()`를 직접 부르지 않는다 — 그 함수는 테스트할 수 없다(6.1)."""

    def now(self) -> datetime:
        """언제나 aware, 사용자 타임존."""
        ...
