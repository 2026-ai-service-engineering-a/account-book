from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """`datetime.now()`를 직접 부르지 않는다. 시계도 포트다(development-rules 6.1)."""

    def now(self) -> datetime:
        """언제나 aware. 사용자 타임존에 맞춘 값이다 — ui는 표시하는 쪽이라서."""
        ...
