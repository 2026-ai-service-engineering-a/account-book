from __future__ import annotations

from collections.abc import Mapping

from api.application.dto import RunRecord
from api.application.ports import Clock, UnitOfWork
from api.domain.errors import RunNotFound
from api.domain.values import RunStatus


class DecideRun:
    """쓰기 제안의 결정 — 확인(`confirmed_at` 채우기)과 닫기(`done`·`aborted`).
    커밋은 멱등 쓰기가 한다.

    `failed`는 확인한 쓰기를 api가 거절한 것이다(422) — 취소가 아니라서 확인됐어도 닫힌다.
    둘 다 "지금 대기일 때만" 바꾸고, 바꿨든 아니든 결정 뒤의 실행을 돌려준다 — agent는 그 상태를
    보고 무엇을 할지 정한다(두 번 누름·재시작·만료). 확인된 제안은 `aborted`로 닫히지 않는다.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def confirm(self, uow: UnitOfWork, run_id: str, call_id: str) -> RunRecord:
        self._exists(uow, run_id)
        uow.runs.confirm(run_id, call_id, self._clock.now())
        return self._exists(uow, run_id)

    def close(
        self,
        uow: UnitOfWork,
        run_id: str,
        status: RunStatus,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]],
    ) -> RunRecord:
        if status not in (RunStatus.DONE, RunStatus.ABORTED, RunStatus.FAILED):
            raise ValueError("제안은 done·aborted·failed로만 닫는다")
        self._exists(uow, run_id)
        uow.runs.close(run_id, status, stop_reason, results)
        return self._exists(uow, run_id)

    @staticmethod
    def _exists(uow: UnitOfWork, run_id: str) -> RunRecord:
        found = uow.runs.get(run_id)
        if found is None:
            raise RunNotFound
        return found
