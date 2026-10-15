from __future__ import annotations

from api.application.dto import RunRecord
from api.application.ports import UnitOfWork


class RecordRun:
    """끝난 에이전트 실행 하나를 감사 로그에 넣는다. 커밋은 부르는 쪽(멱등 쓰기)이 한다.

    agent는 실행마다 키를 `run:{run_id}`로 만든다 — 기록을 다시 보내도 줄이 둘이 되지 않는다.
    """

    def __call__(self, uow: UnitOfWork, run: RunRecord) -> None:
        uow.runs.add(run)
