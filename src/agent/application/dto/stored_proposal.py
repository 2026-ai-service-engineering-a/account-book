from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StoredProposal:
    """감사 테이블에 저장된 쓰기 제안 — 실행 한 줄과 그 `create_transaction` 호출(chat-capture 6장).

    `confirmed_at`이 있는데 아직 대기면 "쓰는 중"이다 — 같은 키로 다시 쓰면 된다.
    """

    run_id: str
    status: str  # awaiting_confirmation · done · aborted · failed
    created_at: datetime
    call_id: str  # create_transaction의 호출 — c{seq}
    args: Mapping[str, object]  # 쓸 칸. 확인 때 이것으로 다시 만든다
    confirmed_at: datetime | None
    utterance: str = ""

    @property
    def waiting(self) -> bool:
        return self.status == "awaiting_confirmation"

    @property
    def idempotency_key(self) -> str:
        """제안 때 정한 키 `{run_id}:{seq}` — 재시도·두 번 누름·재시작이 같은 키를 쓴다."""
        return f"{self.run_id}:{self.call_id.removeprefix('c')}"
