from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunFilter:
    """실행 목록의 거름 — 자리와 상태. 비면 전부. 값의 목록은 api가 정한다(api-contract 6장)."""

    seat: str = ""
    status: str = ""

    @property
    def is_narrowed(self) -> bool:
        return bool(self.seat or self.status)
