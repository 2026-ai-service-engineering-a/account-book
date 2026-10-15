from __future__ import annotations

from typing import Any

from pydantic import AwareDatetime, BaseModel

from agent.application.dto import StoredProposal
from agent.application.errors import LedgerUnavailable


class _Call(BaseModel):
    call_id: str
    tool: str
    args: dict[str, Any]  # 바깥과 닿는 자리라 Any다(development-rules 5.2)
    confirmed_at: AwareDatetime | None


class ProposalReply(BaseModel):
    """api `GET /v1/runs/{id}`(와 confirm·close)의 본문 — 제안으로 읽는다."""

    id: str
    utterance: str
    status: str
    created_at: AwareDatetime
    tool_calls: list[_Call]

    def proposal(self) -> StoredProposal:
        write = next((c for c in self.tool_calls if c.tool == "create_transaction"), None)
        if write is None:
            raise LedgerUnavailable("쓰기 제안이 아닌 실행이다")
        return StoredProposal(
            run_id=self.id,
            status=self.status,
            created_at=self.created_at,
            call_id=write.call_id,
            args=write.args,
            confirmed_at=write.confirmed_at,
            utterance=self.utterance,
        )
