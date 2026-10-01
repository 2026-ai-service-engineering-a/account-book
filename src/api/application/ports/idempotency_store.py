from __future__ import annotations

from typing import Protocol

from api.application.dto import IdempotencyRecord, StoredReply


class IdempotencyStore(Protocol):
    """멱등 키 저장소(api-contract 3장). 실제 쓰기와 같은 트랜잭션에서 쓴다."""

    def find(self, key: str) -> IdempotencyRecord | None: ...

    def claim(self, key: str, request_hash: str) -> None:
        """처리 중으로 잡는다. 다른 요청이 같은 키를 이미 잡았으면 `RequestInProgress`."""
        ...

    def complete(self, key: str, reply: StoredReply) -> None: ...
