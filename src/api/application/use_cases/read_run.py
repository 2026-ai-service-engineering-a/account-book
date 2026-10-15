from __future__ import annotations

from collections.abc import Callable

from api.application.dto import RunRecord
from api.application.ports import UnitOfWork
from api.domain.errors import RunNotFound


class ReadRun:
    """감사 로그의 실행 한 줄과 그 도구 호출들. agent가 다시 떠도 제안을 이걸로 되살린다."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, run_id: str) -> RunRecord:
        with self._unit_of_work() as uow:
            found = uow.runs.get(run_id)
        if found is None:
            raise RunNotFound
        return found
