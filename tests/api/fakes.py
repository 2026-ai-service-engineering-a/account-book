"""api 테스트의 가짜들 — 메모리 위의 작업 단위·저장소·시계. DB 없이 유스케이스를 돌린다."""

from __future__ import annotations

from datetime import datetime
from types import TracebackType
from typing import Self
from zoneinfo import ZoneInfo

from api.application.dto import (
    IdempotencyRecord,
    StoredReply,
    Totals,
    TransactionDraft,
    TransactionPage,
    TransactionQuery,
)
from api.application.errors import RequestInProgress
from api.domain.entities import Account, Category, Transaction
from api.domain.values import AccountId, CategoryId, Direction, Money, Period, TransactionId

from .fake_index import FakeIndex

SEOUL = ZoneInfo("Asia/Seoul")


class FixedProbe:
    def __init__(self, up: bool = True) -> None:
        self.up = up

    def ping(self) -> bool:
        return self.up


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


class FakeStats:
    """메모리의 거래로 실제로 더한다 — 유스케이스 테스트가 숫자까지 본다."""

    def __init__(self, transactions: FakeTransactions) -> None:
        self._transactions = transactions

    def _rows(self, start: datetime | None, end: datetime | None) -> list[Transaction]:
        return [
            t
            for t in self._transactions.rows.values()
            if (start is None or t.occurred_at >= start) and (end is None or t.occurred_at < end)
        ]

    def totals(self, query: TransactionQuery) -> Totals:
        rows = [
            t
            for t in self._rows(query.start, query.end)
            if query.category_id is None or t.category_id == query.category_id
        ]
        return Totals(
            Money.total(t.amount for t in rows if t.direction is Direction.EXPENSE),
            Money.total(t.amount for t in rows if t.direction is Direction.INCOME),
        )

    def spent_by_category(self, start: datetime, end: datetime) -> dict[CategoryId, Money]:
        out: dict[CategoryId, Money] = {}
        for t in self._rows(start, end):
            if t.direction is Direction.EXPENSE:
                out[t.category_id] = out.get(t.category_id, Money(0)) + t.amount
        return out

    def daily_spent(
        self, category_id: CategoryId, start: datetime, end: datetime
    ) -> list[tuple[int, Money]]:
        return [
            (t.occurred_at.astimezone(SEOUL).day, t.amount)
            for t in self._rows(start, end)
            if t.category_id == category_id and t.direction is Direction.EXPENSE
        ]

    def first_occurred_at(self) -> datetime | None:
        return min((t.occurred_at for t in self._transactions.rows.values()), default=None)


class FakeBudgets:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], Money | None] = {}

    def limits(self, period: Period) -> dict[CategoryId, Money]:
        latest: dict[str, tuple[str, Money | None]] = {}
        for (category, month), amount in self.rows.items():
            if month <= str(period) and (category not in latest or month > latest[category][0]):
                latest[category] = (month, amount)
        return {CategoryId(c): a for c, (_, a) in latest.items() if a is not None}

    def set_limit(self, category_id: CategoryId, period: Period, amount: Money | None) -> None:
        self.rows[(category_id, str(period))] = amount


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakeUnitOfWork:
    """메모리 위의 작업 단위. 커밋하지 않고 나가면 이번에 바뀐 것을 되돌린다 — DB처럼.

    부르면 자기 자신을 낸다 — 유스케이스가 받는 작업 단위 공장 자리에 그대로 넘긴다.
    """

    def __init__(self) -> None:
        self.transactions = FakeTransactions()
        self.catalog = FakeCatalog()
        self.idempotency = FakeIdempotency()
        self.stats = FakeStats(self.transactions)
        self.budgets = FakeBudgets()
        self.index = FakeIndex(self.transactions)
        self.commits = 0

    def __call__(self) -> FakeUnitOfWork:
        return self

    def __enter__(self) -> Self:
        self._rows = dict(self.transactions.rows)
        self._records = dict(self.idempotency.records)
        self._budgets = dict(self.budgets.rows)
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
            self.budgets.rows = self._budgets

    def commit(self) -> None:
        self._committed = True
        self.commits += 1
