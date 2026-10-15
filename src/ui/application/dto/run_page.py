from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import PageCursor

from .run_line import RunLine


@dataclass(frozen=True, slots=True)
class RunPage:
    items: tuple[RunLine, ...]
    next_cursor: PageCursor | None  # 없으면 마지막 쪽
