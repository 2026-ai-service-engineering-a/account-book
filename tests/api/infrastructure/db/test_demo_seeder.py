from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from api.application.use_cases import DetectOutliers
from api.domain.values import Money, Period, TimeRange
from api.infrastructure.db.demo_seeder import seed_demo
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.rows import BudgetRow, TransactionRow
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from tests.api.conftest import SEOUL

pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)  # 서울 18시


def test_twelve_months_up_to_now_once(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
        first = seed_demo(connection, NOW, SEOUL)
        again = seed_demo(connection, NOW, SEOUL)  # 이미 거래가 있으면 넣지 않는다
        latest = connection.execute(select(func.max(TransactionRow.occurred_at))).scalar()
        earliest = connection.execute(select(func.min(TransactionRow.occurred_at))).scalar()
        budgets = connection.execute(select(BudgetRow.period)).scalars().all()
    assert first > 200 and again == 0
    # 이상치는 판정하는 달 앞의 여섯 달을 평소로 쓴다 — 여섯 달치로는 어느 달도 판정할 수 없다
    assert latest <= NOW and earliest.astimezone(SEOUL).strftime("%Y-%m") == "2025-11"
    assert set(budgets) == {"2025-11"}  # 가장 이른 달에 두고 이어 쓴다


def test_last_month_has_the_big_one_the_report_should_catch(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
        seed_demo(connection, NOW, SEOUL)
    sessions = SqlUnitOfWork.factory(migrated)
    detect = DetectOutliers(lambda: SqlUnitOfWork(sessions, "Asia/Seoul"), SEOUL)
    september = TimeRange(*Period(2026, 9).bounds(SEOUL))
    found = detect(september)
    assert [(o.transaction.merchant, o.transaction.amount) for o in found.items] == [
        ("전자랜드", Money(890_000))
    ]
    assert found.skipped == ()
