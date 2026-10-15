"""리포트 캐시의 data_version — 더하기·고치기·지우기·예산 바꾸기에 바뀌고 범위 밖에는 그대로다."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from api.domain.values import CategoryId, Money, Period
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from tests.api.infrastructure.db.test_sql_transaction_repository import tx

pytestmark = pytest.mark.integration
START, END = datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC)


def test_the_version_moves_only_with_what_the_report_reads(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    sessions = SqlUnitOfWork.factory(migrated)

    def version() -> str:
        with SqlUnitOfWork(sessions) as uow:
            return uow.stats.data_version(START, END)

    def write(change: Callable[[SqlUnitOfWork], object]) -> None:
        with SqlUnitOfWork(sessions) as uow:
            change(uow)
            uow.commit()

    empty = version()
    write(lambda uow: uow.transactions.add(tx(1)))
    added = version()
    assert added != empty and added == version()  # 아무것도 안 바뀌면 그대로
    write(lambda uow: uow.transactions.replace(dataclasses.replace(tx(1), amount=Money(9999))))
    edited = version()
    assert edited != added  # 고친 거래 — 건수는 같아도 updated_at이 움직였다
    outside = dataclasses.replace(tx(2), occurred_at=datetime(2026, 11, 3, tzinfo=UTC))
    write(lambda uow: uow.transactions.add(outside))
    assert version() == edited  # 범위 밖 거래는 이 리포트를 바꾸지 않는다
    write(lambda uow: uow.budgets.set_limit(CategoryId("food"), Period(2026, 9), Money(300000)))
    budgeted = version()
    assert budgeted != edited
    write(lambda uow: uow.budgets.set_limit(CategoryId("food"), Period(2026, 9), Money(250000)))
    assert version() != budgeted  # upsert도 updated_at을 움직인다
    write(lambda uow: uow.transactions.remove(tx(1).id))
    assert version() not in {empty, added, edited, budgeted}
