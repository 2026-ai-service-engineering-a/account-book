from __future__ import annotations

from collections.abc import Callable

from api.application.dto import RunPage, RunQuery
from api.application.ports import UnitOfWork
from api.domain.values import RunSeat, RunStatus

DEFAULT_LIMIT = 30
MAX_LIMIT = 100


class ListRuns:
    """감사 로그의 실행 목록 — 최신순, 자리·상태로 거른다. 실행 기록 화면이 읽는다
    (ui_docs/pages/runs.md). 읽기만 한다."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self,
        seat: RunSeat | None = None,
        status: RunStatus | None = None,
        cursor: str | None = None,
        limit: int = DEFAULT_LIMIT,
    ) -> RunPage:
        query = RunQuery(seat, status, cursor, max(1, min(limit, MAX_LIMIT)))
        with self._unit_of_work() as uow:
            return uow.runs.page(query)
