from __future__ import annotations

from pydantic import BaseModel

from ui.application.dto import RunPage
from ui.application.values import PageCursor

from .run_line_reply import RunLineReply


class RunPageReply(BaseModel):
    """api `GET /v1/runs`의 응답 — 줄마다 도구 호출의 수만."""

    items: list[RunLineReply]
    next_cursor: str | None

    def page(self) -> RunPage:
        cursor = PageCursor(self.next_cursor) if self.next_cursor else None
        return RunPage(tuple(i.line() for i in self.items), cursor)
