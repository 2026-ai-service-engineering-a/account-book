from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from .catalog_repository import CatalogRepository
from .idempotency_store import IdempotencyStore
from .transaction_repository import TransactionRepository


class UnitOfWork(Protocol):
    """DB 트랜잭션 하나. `commit()`을 부르지 않고 나가면 전부 되돌린다.

    멱등 키 저장과 실제 쓰기가 같은 트랜잭션이어야 한다 — 따로 커밋하면 그 사이에 중복이
    들어간다(api-contract 3장).
    """

    # 읽기 전용 — 구현이 더 좁은 타입(SqlTransactionRepository)을 들고 있어도 맞는다
    @property
    def transactions(self) -> TransactionRepository: ...

    @property
    def catalog(self) -> CatalogRepository: ...

    @property
    def idempotency(self) -> IdempotencyStore: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...
