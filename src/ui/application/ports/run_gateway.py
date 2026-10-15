from __future__ import annotations

from typing import Protocol

from ui.application.dto import RunDetail, RunFilter, RunPage
from ui.application.values import PageCursor, RunId


class RunGateway(Protocol):
    """api의 `/v1/runs` — 읽기만 한다. 실행 기록 화면이 읽는다(ui_docs/pages/runs.md).

    쓰는 메서드가 없다. 확인 대기인 제안도 여기서 확인하지 않는다 — 확인은 채팅의 카드가 한다.
    """

    async def page(
        self, criteria: RunFilter, cursor: PageCursor | None = None, limit: int = 30
    ) -> RunPage: ...

    async def get(self, run_id: RunId) -> RunDetail | None:
        """없으면 None."""
        ...
