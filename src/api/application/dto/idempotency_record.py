from __future__ import annotations

from dataclasses import dataclass

from .stored_reply import StoredReply


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """저장된 키 하나. `reply`가 없으면 아직 처리 중이다."""

    request_hash: str
    reply: StoredReply | None
