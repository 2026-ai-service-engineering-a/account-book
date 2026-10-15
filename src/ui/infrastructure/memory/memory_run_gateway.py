from __future__ import annotations

from ui.application.dto import RunDetail, RunFilter, RunPage
from ui.application.values import PageCursor, RunId


class MemoryRunGateway:
    """api 자리의 대역. 감사 로그가 없다 — 각본 대역은 실행을 남기지 않는다(ui_docs/stand-ins.md).
    실행 기록 화면은 첫날처럼 비어 보인다."""

    async def page(
        self, criteria: RunFilter, cursor: PageCursor | None = None, limit: int = 30
    ) -> RunPage:
        return RunPage((), None)

    async def get(self, run_id: RunId) -> RunDetail | None:
        return None
