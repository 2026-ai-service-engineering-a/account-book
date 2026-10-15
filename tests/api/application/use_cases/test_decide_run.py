from __future__ import annotations

from datetime import UTC, datetime

import pytest

from api.application.dto import ToolCallRecord
from api.application.use_cases import DecideRun
from api.domain.errors import RunNotFound
from api.domain.values import RunSeat, RunStatus
from tests.api.application.dto.test_run_record import run_record
from tests.api.conftest import FakeUnitOfWork, FixedClock

NOW = datetime(2026, 10, 15, 3, tzinfo=UTC)
WRITE = ToolCallRecord("c2", "create_transaction", {"amount": 8500}, None)


def proposed(run_id: str = "r1") -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    uow.runs.add(
        run_record(
            run_id,
            seat=RunSeat.CAPTURE,
            status=RunStatus.AWAITING_CONFIRMATION,
            stop_reason="proposed",
            tool_calls=(WRITE,),
        )
    )
    return uow


def test_confirm_stamps_once_and_keeps_the_first_time():
    uow, decide = proposed(), DecideRun(FixedClock(NOW))
    first = decide.confirm(uow, "r1", "c2")
    later = DecideRun(FixedClock(datetime(2026, 10, 15, 4, tzinfo=UTC))).confirm(uow, "r1", "c2")
    assert first.tool_calls[0].confirmed_at == NOW == later.tool_calls[0].confirmed_at


def test_a_confirmed_proposal_is_not_cancelled_but_can_be_done():
    uow, decide = proposed(), DecideRun(FixedClock(NOW))
    decide.confirm(uow, "r1", "c2")
    kept = decide.close(uow, "r1", RunStatus.ABORTED, "cancelled", {})
    assert kept.status is RunStatus.AWAITING_CONFIRMATION
    done = decide.close(uow, "r1", RunStatus.DONE, "confirmed", {"c2": {"id": "t1"}})
    assert (done.status, done.tool_calls[0].result) == (RunStatus.DONE, {"id": "t1"})


def test_closed_runs_stay_closed():
    uow, decide = proposed(), DecideRun(FixedClock(NOW))
    decide.close(uow, "r1", RunStatus.ABORTED, "cancelled", {})
    assert decide.confirm(uow, "r1", "c2").tool_calls[0].confirmed_at is None
    again = decide.close(uow, "r1", RunStatus.DONE, "confirmed", {})
    assert (again.status, again.stop_reason) == (RunStatus.ABORTED, "cancelled")


def test_only_done_or_aborted_and_only_known_runs():
    uow, decide = proposed(), DecideRun(FixedClock(NOW))
    with pytest.raises(ValueError):
        decide.close(uow, "r1", RunStatus.FAILED, "x", {})
    with pytest.raises(RunNotFound):
        decide.confirm(uow, "nope", "c2")
