from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import exists, func, select, tuple_, update
from sqlalchemy.orm import Session

from api.application.dto import RunPage, RunQuery, RunRecord, RunSummary, ToolCallRecord
from api.domain.values import RunFlow, RunSeat, RunStatus

from .page_cursor import decode_cursor, encode_cursor
from .rows import AgentRunRow, ToolCallRow

_WAITING = RunStatus.AWAITING_CONFIRMATION.value


class SqlRunLog:
    """감사 로그를 Postgres에. 실행과 도구 호출이 같은 세션 — 한 트랜잭션에 들어간다.

    고치는 문장은 전부 "지금 대기일 때만"을 WHERE에 건다 — 두 요청이 겹쳐도 한쪽만 바꾼다.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, run: RunRecord) -> None:
        self._session.add(
            AgentRunRow(
                id=run.id,
                seat=run.seat.value,
                flow=run.flow.value,
                utterance=run.utterance,
                model=run.model,
                steps=run.steps,
                tokens=run.tokens,
                cost_usd=run.cost_usd,
                status=run.status.value,
                stop_reason=run.stop_reason,
                client=run.client,
            )
        )
        # 실행 줄이 먼저 있어야 외래 키가 맞는다
        self._session.flush()
        self._session.add_all(
            ToolCallRow(
                run_id=run.id,
                call_id=c.call_id,
                tool=c.tool,
                args=dict(c.args),
                result=dict(c.result) if c.result is not None else None,
            )
            for c in run.tool_calls
        )

    def get(self, run_id: str) -> RunRecord | None:
        row = self._session.get(AgentRunRow, run_id)
        if row is None:
            return None
        calls = self._session.scalars(
            select(ToolCallRow).where(ToolCallRow.run_id == run_id).order_by(ToolCallRow.id)
        )
        return _record(
            row,
            tuple(
                ToolCallRecord(c.call_id, c.tool, c.args, c.result, c.confirmed_at) for c in calls
            ),
        )

    def page(self, query: RunQuery) -> RunPage:
        counted = (
            select(func.count(ToolCallRow.id))
            .where(ToolCallRow.run_id == AgentRunRow.id)
            .correlate(AgentRunRow)
            .scalar_subquery()
        )
        statement = select(AgentRunRow, counted)
        if query.seat is not None:
            statement = statement.where(AgentRunRow.seat == query.seat.value)
        if query.status is not None:
            statement = statement.where(AgentRunRow.status == query.status.value)
        after = decode_cursor(query.cursor) if query.cursor else None
        if after is not None:
            statement = statement.where(
                tuple_(AgentRunRow.created_at, AgentRunRow.id) < tuple_(*after)
            )
        statement = statement.order_by(AgentRunRow.created_at.desc(), AgentRunRow.id.desc()).limit(
            query.limit + 1
        )  # 하나 더 읽어 다음 쪽이 있는지 안다
        rows: Sequence[tuple[AgentRunRow, int]] = self._session.execute(statement).all()
        page, more = rows[: query.limit], len(rows) > query.limit
        last = page[-1][0] if page else None
        cursor = encode_cursor(last.created_at, last.id) if more and last else None
        return RunPage(tuple(RunSummary(_record(r, ()), n) for r, n in page), cursor)

    def confirm(self, run_id: str, call_id: str, at: datetime) -> None:
        waiting = exists().where(AgentRunRow.id == run_id, AgentRunRow.status == _WAITING)
        self._session.execute(
            update(ToolCallRow)
            .where(
                ToolCallRow.run_id == run_id,
                ToolCallRow.call_id == call_id,
                ToolCallRow.confirmed_at.is_(None),
                waiting,
            )
            .values(confirmed_at=at)
        )

    def close(
        self,
        run_id: str,
        status: RunStatus,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]],
    ) -> None:
        conditions = [AgentRunRow.id == run_id, AgentRunRow.status == _WAITING]
        if status is RunStatus.ABORTED:
            confirmed = exists().where(
                ToolCallRow.run_id == run_id, ToolCallRow.confirmed_at.is_not(None)
            )
            conditions.append(~confirmed)
        closed = self._session.execute(
            update(AgentRunRow)
            .where(*conditions)
            .values(status=status.value, stop_reason=stop_reason)
            .returning(AgentRunRow.id)
        ).first()
        if closed is None:
            return
        for call_id, result in results.items():
            self._session.execute(
                update(ToolCallRow)
                .where(ToolCallRow.run_id == run_id, ToolCallRow.call_id == call_id)
                .values(result=dict(result))
            )


def _record(row: AgentRunRow, calls: tuple[ToolCallRecord, ...]) -> RunRecord:
    return RunRecord(
        id=row.id,
        seat=RunSeat(row.seat),
        flow=RunFlow(row.flow),
        utterance=row.utterance,
        model=row.model,
        steps=row.steps,
        tokens=row.tokens,
        cost_usd=Decimal(row.cost_usd),
        status=RunStatus(row.status),
        stop_reason=row.stop_reason,
        tool_calls=calls,
        client=row.client,
        created_at=row.created_at,
    )
