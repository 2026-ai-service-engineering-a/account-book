from __future__ import annotations

import secrets
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Self
from zoneinfo import ZoneInfo

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text

from api.application.dto import (
    IdempotencyRecord,
    StoredReply,
    TransactionDraft,
    TransactionPage,
    TransactionQuery,
)
from api.application.errors import RequestInProgress
from api.application.ports import DatabaseProbe, UnitOfWork
from api.domain.entities import Account, Category, Transaction
from api.domain.values import AccountId, CategoryId, Direction, Money, TransactionId
from api.infrastructure.settings import Settings
from api.main import create_app

SEOUL = ZoneInfo("Asia/Seoul")

ALEMBIC_INI = Path(__file__).parents[2] / "src" / "api" / "alembic.ini"


class FixedProbe:
    def __init__(self, up: bool = True) -> None:
        self.up = up

    def ping(self) -> bool:
        return self.up


def migrate(engine: Engine, revision: str = "head", down: bool = False) -> None:
    """env.py가 이 연결로 돈다 — 개발용 DB가 아니라 테스트가 만든 DB다."""
    config = Config(str(ALEMBIC_INI))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        if down:
            command.downgrade(config, revision)
        else:
            command.upgrade(config, revision)


@pytest.fixture
def database() -> Iterator[Engine]:
    """테스트마다 빈 DB를 하나 만들고 끝나면 지운다. 개발용 DB의 데이터는 건드리지 않는다.

    compose의 db가 떠 있어야 한다(-m integration). 만드는 권한은 POSTGRES_USER에 있다.
    """
    settings = Settings()
    name = f"test_{secrets.token_hex(6)}"
    admin = create_engine(settings.database_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(settings.database_url(name))
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def migrated(database: Engine) -> Engine:
    migrate(database)
    return database


def draft(
    amount: int = 8_500,
    category: str = "food",
    direction: Direction = Direction.EXPENSE,
    account: str = "card",
    merchant: str = "김밥천국",
    at: datetime | None = None,
) -> TransactionDraft:
    return TransactionDraft(
        direction=direction,
        amount=Money(amount),
        occurred_at=at or datetime(2026, 9, 16, 12, 30, tzinfo=SEOUL),
        category_id=CategoryId(category),
        account_id=AccountId(account),
        merchant=merchant,
    )


class FakeCatalog:
    def categories(self, direction: Direction | None = None) -> tuple[Category, ...]:
        rows = (
            Category(CategoryId("food"), "식비", Direction.EXPENSE),
            Category(CategoryId("cafe"), "카페", Direction.EXPENSE),
            Category(CategoryId("salary"), "급여", Direction.INCOME),
        )
        return tuple(c for c in rows if direction is None or c.direction == direction)

    def accounts(self) -> tuple[Account, ...]:
        return (Account(AccountId("card"), "카드", "card"),)


class FakeTransactions:
    def __init__(self) -> None:
        self.rows: dict[str, Transaction] = {}

    def get(self, transaction_id: TransactionId) -> Transaction | None:
        return self.rows.get(transaction_id)

    def search(self, query: TransactionQuery) -> TransactionPage:
        self.last_query = query
        return TransactionPage(tuple(self.rows.values())[: query.limit], None)

    def add(self, transaction: Transaction) -> None:
        self.rows[transaction.id] = transaction

    def replace(self, transaction: Transaction) -> None:
        self.rows[transaction.id] = transaction

    def remove(self, transaction_id: TransactionId) -> None:
        del self.rows[transaction_id]


class FakeIdempotency:
    def __init__(self) -> None:
        self.records: dict[str, IdempotencyRecord] = {}

    def find(self, key: str) -> IdempotencyRecord | None:
        return self.records.get(key)

    def claim(self, key: str, request_hash: str) -> None:
        if key in self.records:
            raise RequestInProgress
        self.records[key] = IdempotencyRecord(request_hash, None)

    def complete(self, key: str, reply: StoredReply) -> None:
        self.records[key] = IdempotencyRecord(self.records[key].request_hash, reply)


class FakeUnitOfWork:
    """메모리 위의 작업 단위. 커밋하지 않고 나가면 이번에 바뀐 것을 되돌린다 — DB처럼."""

    def __init__(self) -> None:
        self.transactions = FakeTransactions()
        self.catalog = FakeCatalog()
        self.idempotency = FakeIdempotency()
        self.commits = 0

    def __call__(self) -> FakeUnitOfWork:
        return self

    def __enter__(self) -> Self:
        self._rows = dict(self.transactions.rows)
        self._records = dict(self.idempotency.records)
        self._committed = False
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        if not self._committed:
            self.transactions.rows = self._rows
            self.idempotency.records = self._records

    def commit(self) -> None:
        self._committed = True
        self.commits += 1


def client_with(
    uow: Callable[[], UnitOfWork] | None = None, database: DatabaseProbe | None = None
) -> TestClient:
    """가짜 작업 단위로 조립한 api. 비밀번호는 쓰지 않지만 설정이 요구한다."""
    settings = Settings(_env_file=None, postgres_password=SecretStr("unused"))
    app = create_app(
        settings, database=database or FixedProbe(), unit_of_work=uow or FakeUnitOfWork()
    )
    return TestClient(app, raise_server_exceptions=False)
