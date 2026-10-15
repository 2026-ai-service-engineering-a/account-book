"""감사 테이블의 가짜 — RunRecorder이면서 ProposalBook이다. api처럼 "지금 대기일 때만" 고치고,
확인된 제안은 aborted로 닫지 않는다. 같은 표를 새 DecideRecord에 끼우면 재시작이다."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from agent.application.dto import RunRecord, StoredProposal
from agent.application.ports.proposal_book import Closing


@dataclasses.dataclass
class _Row:
    run: RunRecord
    status: str
    stop_reason: str
    created_at: datetime
    confirmed_at: dict[str, datetime] = dataclasses.field(default_factory=dict)
    results: dict[str, Mapping[str, object]] = dataclasses.field(default_factory=dict)


class FakeAuditTable:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime(2026, 10, 15, 3, tzinfo=UTC))
        self.rows: dict[str, _Row] = {}
        self.fail: Exception | None = None  # 주면 저장(record)이 그것을 던진다

    async def record(self, run: RunRecord, model: str) -> None:
        if self.fail is not None:
            raise self.fail
        status = "failed" if run.failed else "awaiting_confirmation" if run.awaiting else "done"
        self.rows[run.run_id] = _Row(run, status, run.stop_reason, self._clock())

    async def get(self, run_id: str) -> StoredProposal | None:
        row = self.rows.get(run_id)
        return _proposal(row) if row is not None else None

    async def confirm(self, run_id: str, call_id: str) -> StoredProposal:
        row = self.rows[run_id]
        if row.status == "awaiting_confirmation":
            row.confirmed_at.setdefault(call_id, self._clock())
        return _proposal(row)

    async def close(
        self,
        run_id: str,
        status: Closing,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]] | None = None,
    ) -> StoredProposal:
        row = self.rows[run_id]
        if row.status == "awaiting_confirmation" and not (status == "aborted" and row.confirmed_at):
            row.status, row.stop_reason = status, stop_reason
            row.results.update(results or {})
        return _proposal(row)

    def status_of(self, run_id: str) -> tuple[str, str]:
        row = self.rows[run_id]
        return row.status, row.stop_reason


def _proposal(row: _Row) -> StoredProposal:
    write = next(c for c in row.run.tool_calls if c.tool == "create_transaction")
    return StoredProposal(
        run_id=row.run.run_id,
        status=row.status,
        created_at=row.created_at,
        call_id=write.call_id,
        args=write.args,
        confirmed_at=row.confirmed_at.get(write.call_id),
        utterance=row.run.utterance,
    )
