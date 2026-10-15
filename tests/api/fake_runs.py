"""감사 로그의 가짜 — 메모리 위의 실행. SqlRunLog처럼 "지금 대기일 때만" 고친다."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import UTC, datetime

from api.application.dto import RunPage, RunQuery, RunRecord, RunSummary
from api.domain.values import RunStatus
from api.infrastructure.db.page_cursor import decode_cursor, encode_cursor

_WAITING = RunStatus.AWAITING_CONFIRMATION


class FakeRuns:
    def __init__(self, now: datetime | None = None) -> None:
        self.rows: dict[str, RunRecord] = {}
        self._now = now or datetime(2026, 10, 15, 3, tzinfo=UTC)

    def add(self, run: RunRecord) -> None:
        if run.id in self.rows:
            raise ValueError("같은 실행이 두 번 들어왔다 — DB라면 기본 키에 걸린다")
        self.rows[run.id] = dataclasses.replace(run, created_at=run.created_at or self._now)

    def get(self, run_id: str) -> RunRecord | None:
        return self.rows.get(run_id)

    def page(self, query: RunQuery) -> RunPage:
        def key(run: RunRecord) -> tuple[datetime, str]:
            return (run.created_at or self._now, run.id)

        found = sorted(
            (
                r
                for r in self.rows.values()
                if (query.seat is None or r.seat is query.seat)
                and (query.status is None or r.status is query.status)
            ),
            key=key,
            reverse=True,
        )
        after = decode_cursor(query.cursor) if query.cursor else None
        if after is not None:
            found = [r for r in found if key(r) < after]
        page, more = found[: query.limit], len(found) > query.limit
        cursor = encode_cursor(*key(page[-1])) if more and page else None
        lines = tuple(
            RunSummary(dataclasses.replace(r, tool_calls=()), len(r.tool_calls)) for r in page
        )
        return RunPage(lines, cursor)

    def confirm(self, run_id: str, call_id: str, at: datetime) -> None:
        run = self.rows.get(run_id)
        if run is None or run.status is not _WAITING:
            return
        calls = tuple(
            dataclasses.replace(c, confirmed_at=at)
            if c.call_id == call_id and c.confirmed_at is None
            else c
            for c in run.tool_calls
        )
        self.rows[run_id] = dataclasses.replace(run, tool_calls=calls)

    def close(
        self,
        run_id: str,
        status: RunStatus,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]],
    ) -> None:
        run = self.rows.get(run_id)
        if run is None or run.status is not _WAITING:
            return
        if status is RunStatus.ABORTED and any(c.confirmed_at for c in run.tool_calls):
            return
        calls = tuple(
            dataclasses.replace(c, result=results[c.call_id]) if c.call_id in results else c
            for c in run.tool_calls
        )
        self.rows[run_id] = dataclasses.replace(
            run, status=status, stop_reason=stop_reason, tool_calls=calls
        )
