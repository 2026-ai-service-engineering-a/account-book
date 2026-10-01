from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from .sql_budget_repository import SqlBudgetRepository
from .sql_catalog_repository import SqlCatalogRepository
from .sql_category_index import SqlCategoryIndex
from .sql_idempotency_store import SqlIdempotencyStore
from .sql_stats_repository import SqlStatsRepository
from .sql_transaction_repository import SqlTransactionRepository


class SqlUnitOfWork:
    """세션 하나 = DB 트랜잭션 하나. `commit()` 없이 나가면 되돌린다.

    저장소들이 같은 세션을 나눠 쓴다 — 멱등 키와 거래(예산)가 한 트랜잭션에 들어간다.
    `zone_name`은 집계의 "그날"을 정하는 사용자 타임존이다.
    """

    transactions: SqlTransactionRepository
    catalog: SqlCatalogRepository
    idempotency: SqlIdempotencyStore
    stats: SqlStatsRepository
    budgets: SqlBudgetRepository
    index: SqlCategoryIndex

    def __init__(self, sessions: sessionmaker[Session], zone_name: str = "Asia/Seoul") -> None:
        self._sessions = sessions
        self._zone_name = zone_name
        self._session: Session | None = None

    @classmethod
    def factory(cls, engine: Engine) -> sessionmaker[Session]:
        # 커밋 뒤에도 읽은 값을 쓴다 — 응답을 만들려고 다시 조회하지 않게
        return sessionmaker(bind=engine, expire_on_commit=False)

    def __enter__(self) -> Self:
        session = self._sessions()
        self._session = session
        self.transactions = SqlTransactionRepository(session)
        self.catalog = SqlCatalogRepository(session)
        self.idempotency = SqlIdempotencyStore(session)
        self.stats = SqlStatsRepository(session, self._zone_name)
        self.budgets = SqlBudgetRepository(session)
        self.index = SqlCategoryIndex(session)
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        if self._session is not None:
            self._session.rollback()  # 커밋한 뒤면 할 일이 없다
            self._session.close()
            self._session = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("with 블록 밖에서 commit을 불렀다")
        self._session.commit()
