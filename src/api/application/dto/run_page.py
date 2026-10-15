from __future__ import annotations

from dataclasses import dataclass

from .run_summary import RunSummary


@dataclass(frozen=True, slots=True)
class RunPage:
    items: tuple[RunSummary, ...]
    next_cursor: str | None  # 없으면 마지막 쪽
