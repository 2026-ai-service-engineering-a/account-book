from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.application.dto import ToolCallRecord
from api.application.use_cases import ListRuns
from api.domain.values import RunSeat, RunStatus
from tests.api.application.dto.test_run_record import run_record
from tests.api.conftest import FakeUnitOfWork

START = datetime(2026, 10, 15, 3, tzinfo=UTC)


def five_runs() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    seats = [RunSeat.CHAT, RunSeat.MCP, RunSeat.CHAT, RunSeat.INSIGHT, RunSeat.CHAT]
    for n, seat in enumerate(seats):
        status = RunStatus.FAILED if n == 2 else RunStatus.DONE
        calls = tuple(ToolCallRecord(f"c{i}", "summarize_spending", {}, None) for i in range(n))
        at = START + timedelta(minutes=n)
        uow.runs.add(run_record(f"r{n}", seat=seat, status=status, tool_calls=calls, created_at=at))
    return uow


def test_newest_first_with_the_number_of_calls_only():
    page = ListRuns(five_runs())()
    assert [line.run.id for line in page.items] == ["r4", "r3", "r2", "r1", "r0"]
    assert [line.tool_count for line in page.items] == [4, 3, 2, 1, 0]
    assert all(line.run.tool_calls == () for line in page.items)
    assert page.next_cursor is None


def test_filters_by_seat_and_status():
    uow = five_runs()
    assert [x.run.id for x in ListRuns(uow)(seat=RunSeat.CHAT).items] == ["r4", "r2", "r0"]
    chat_failed = ListRuns(uow)(seat=RunSeat.CHAT, status=RunStatus.FAILED)
    assert [x.run.id for x in chat_failed.items] == ["r2"]


def test_pages_follow_the_cursor_without_overlap():
    uow = five_runs()
    first = ListRuns(uow)(limit=2)
    second = ListRuns(uow)(cursor=first.next_cursor, limit=2)
    third = ListRuns(uow)(cursor=second.next_cursor, limit=2)
    ids = [x.run.id for p in (first, second, third) for x in p.items]
    assert ids == ["r4", "r3", "r2", "r1", "r0"] and third.next_cursor is None


def test_the_limit_is_clamped():
    assert len(ListRuns(five_runs())(limit=0).items) == 1
