from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, Protocol

from agent.application.dto import StoredProposal

type Closing = Literal["done", "aborted", "failed"]


class ProposalBook(Protocol):
    """쓰기 제안을 두는 곳 — api의 감사 테이블(chat-capture 결정 5). agent는 DB를 모른다.

    고치는 둘은 "지금 대기일 때만" 바꾸고 결정 뒤의 제안을 돌려준다. 바뀌었는지는 돌려받은 상태로
    안다. 닿지 못하면 `LedgerUnavailable`.
    """

    async def get(self, run_id: str) -> StoredProposal | None: ...

    async def confirm(self, run_id: str, call_id: str) -> StoredProposal:
        """`confirmed_at`을 비어 있을 때만 채운다."""
        ...

    async def close(
        self,
        run_id: str,
        status: Closing,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]] | None = None,
    ) -> StoredProposal:
        """확인된 제안은 aborted로 닫히지 않는다. failed는 거절된 쓰기다.
        `results`는 call_id → 결과."""
        ...
