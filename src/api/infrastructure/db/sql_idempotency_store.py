from __future__ import annotations

from sqlalchemy import delete, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.application.dto import IdempotencyRecord, StoredReply
from api.application.errors import RequestInProgress

from .rows import IdempotencyKeyRow

# 키는 24시간 산다(api-contract 3장). 그 뒤 같은 키는 새 요청이다.
_RETENTION = text("interval '24 hours'")


class SqlIdempotencyStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find(self, key: str) -> IdempotencyRecord | None:
        # 지난 키는 찾는 김에 지운다. 따로 도는 청소 작업을 두지 않는다
        self._session.execute(
            delete(IdempotencyKeyRow).where(
                IdempotencyKeyRow.key == key,
                IdempotencyKeyRow.created_at < func.now() - _RETENTION,
            )
        )
        row = self._session.get(IdempotencyKeyRow, key)
        if row is None:
            return None
        reply = None
        if row.status_code is not None:
            reply = StoredReply(row.status_code, row.response)
        return IdempotencyRecord(row.request_hash, reply)

    def claim(self, key: str, request_hash: str) -> None:
        """같은 키를 동시에 잡으면 늦은 쪽은 앞선 쪽이 끝날 때까지 기다렸다가 여기서 걸린다."""
        self._session.add(IdempotencyKeyRow(key=key, request_hash=request_hash))
        try:
            self._session.flush()
        except IntegrityError as error:
            raise RequestInProgress from error

    def complete(self, key: str, reply: StoredReply) -> None:
        row = self._session.get(IdempotencyKeyRow, key)
        if row is None:  # claim한 같은 트랜잭션 안이다. 여기 오면 순서가 틀렸다
            raise RuntimeError("claim 없이 complete를 불렀다")
        row.status_code = reply.status_code
        row.response = dict(reply.body) if reply.body is not None else None
        self._session.flush()
