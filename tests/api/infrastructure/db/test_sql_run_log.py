from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.application.dto import ToolCallRecord
from api.infrastructure.db.rows import AgentRunRow, ToolCallRow
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from tests.api.application.dto.test_run_record import run_record

pytestmark = pytest.mark.integration


def test_puts_the_run_and_its_calls_in_one_transaction(migrated):
    calls = (
        ToolCallRecord("c1", "summarize_spending", {"q": "카페"}, {"ok": True}),
        ToolCallRecord("c2__thought__" + "x" * 200, "summarize_spending", {"q": "카페"}, None),
    )
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        uow.runs.add(run_record("r1", tool_calls=calls))
        uow.commit()
    with migrated.connect() as connection:
        run = connection.execute(select(AgentRunRow.seat, AgentRunRow.stop_reason)).one()
        rows = connection.execute(
            select(ToolCallRow.call_id, ToolCallRow.result).order_by(ToolCallRow.id)
        ).all()
    assert tuple(run) == ("chat", "answered")
    # 제공자의 call_id는 길다 — Gemini는 생각 서명을 붙인다
    assert [tuple(r) for r in rows] == [("c1", {"ok": True}), ("c2__thought__" + "x" * 200, None)]


def test_the_same_run_twice_is_refused(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        uow.runs.add(run_record("r1"))
        uow.commit()
    with pytest.raises(IntegrityError), SqlUnitOfWork(sessions) as uow:
        uow.runs.add(run_record("r1"))
        uow.commit()


def test_only_a_waiting_run_is_stamped_and_closed(migrated):
    from datetime import UTC, datetime

    from api.domain.values import RunSeat, RunStatus

    write = ToolCallRecord("c2", "create_transaction", {"amount": 8500}, None)
    sessions = SqlUnitOfWork.factory(migrated)
    waiting = run_record(
        "r1",
        seat=RunSeat.CAPTURE,
        status=RunStatus.AWAITING_CONFIRMATION,
        stop_reason="proposed",
        tool_calls=(write,),
    )
    first, later = datetime(2026, 10, 15, 3, tzinfo=UTC), datetime(2026, 10, 15, 4, tzinfo=UTC)
    with SqlUnitOfWork(sessions) as uow:
        uow.runs.add(waiting)
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        uow.runs.confirm("r1", "c2", first)
        uow.runs.confirm("r1", "c2", later)  # 두 번 눌러도 처음 시각
        uow.runs.close("r1", RunStatus.ABORTED, "cancelled", {})  # 확인된 제안은 취소되지 않는다
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        run = uow.runs.get("r1")
        assert run is not None and run.status is RunStatus.AWAITING_CONFIRMATION
        assert run.tool_calls[0].confirmed_at == first and run.created_at is not None
        uow.runs.close("r1", RunStatus.DONE, "confirmed", {"c2": {"id": "t1"}})
        uow.runs.close("r1", RunStatus.ABORTED, "late", {})  # 닫힌 뒤에는 그대로
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        run = uow.runs.get("r1")
        assert run is not None and (run.status, run.stop_reason) == (RunStatus.DONE, "confirmed")
        assert run.tool_calls[0].result == {"id": "t1"}


def test_keeps_the_mcp_clients_name(migrated):
    from api.domain.values import RunFlow, RunSeat

    sessions = SqlUnitOfWork.factory(migrated)
    mcp = run_record("r1", seat=RunSeat.MCP, flow=RunFlow.DIRECT, utterance="", client="Claude")
    with SqlUnitOfWork(sessions) as uow:
        uow.runs.add(mcp)
        uow.runs.add(run_record("r2"))
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        first, second = uow.runs.get("r1"), uow.runs.get("r2")
    assert first is not None and (first.seat, first.client) == (RunSeat.MCP, "Claude")
    assert second is not None and second.client is None


def test_pages_newest_first_with_the_call_count(migrated):
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import update

    from api.application.dto import RunQuery
    from api.domain.values import RunSeat

    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        for n in range(3):
            seat = RunSeat.MCP if n == 1 else RunSeat.CHAT
            calls = tuple(ToolCallRecord(f"c{i}", "summarize_spending", {}, None) for i in range(n))
            uow.runs.add(run_record(f"r{n}", seat=seat, tool_calls=calls))
        uow.commit()
    # created_at은 DB가 채운다 — 한 트랜잭션이면 같은 시각이라 순서를 맞춰 둔다
    start = datetime(2026, 10, 15, 3, tzinfo=UTC)
    with migrated.begin() as connection:
        for n in range(3):
            connection.execute(
                update(AgentRunRow)
                .where(AgentRunRow.id == f"r{n}")
                .values(created_at=start + timedelta(minutes=n))
            )
    with SqlUnitOfWork(sessions) as uow:
        first = uow.runs.page(RunQuery(limit=2))
        rest = uow.runs.page(RunQuery(cursor=first.next_cursor, limit=2))
        chat = uow.runs.page(RunQuery(seat=RunSeat.CHAT))
    assert [(x.run.id, x.tool_count) for x in first.items] == [("r2", 2), ("r1", 1)]
    assert [x.run.id for x in rest.items] == ["r0"] and rest.next_cursor is None
    assert [x.run.id for x in chat.items] == ["r2", "r0"]
    assert first.items[0].run.tool_calls == ()
