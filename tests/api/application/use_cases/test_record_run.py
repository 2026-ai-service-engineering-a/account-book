from __future__ import annotations

from api.application.use_cases import RecordRun
from tests.api.application.dto.test_run_record import run_record
from tests.api.conftest import FakeUnitOfWork


def test_adds_the_run_and_leaves_the_commit_to_the_caller():
    uow = FakeUnitOfWork()
    with uow:
        RecordRun()(uow, run_record())
    # 커밋하지 않고 나갔으니 되돌아간다 — 커밋은 멱등 쓰기의 몫이다
    assert uow.runs.rows == {}
    with uow:
        RecordRun()(uow, run_record())
        uow.commit()
    assert set(uow.runs.rows) == {"r1"}
