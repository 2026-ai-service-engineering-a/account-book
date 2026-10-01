from __future__ import annotations

from typing import Protocol


class DatabaseProbe(Protocol):
    """DB에 닿는지만 본다. api는 동기라 포트도 동기다(development-rules 6.2)."""

    def ping(self) -> bool: ...
