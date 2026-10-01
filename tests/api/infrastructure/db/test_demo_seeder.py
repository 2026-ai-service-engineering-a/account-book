from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from api.infrastructure.db.demo_seeder import seed_demo
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.rows import BudgetRow, TransactionRow
from tests.api.conftest import SEOUL

pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)  # 서울 18시


def test_six_months_up_to_now_once(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
        first = seed_demo(connection, NOW, SEOUL)
        again = seed_demo(connection, NOW, SEOUL)  # 이미 거래가 있으면 넣지 않는다
        latest = connection.execute(select(func.max(TransactionRow.occurred_at))).scalar()
        earliest = connection.execute(select(func.min(TransactionRow.occurred_at))).scalar()
        budgets = connection.execute(select(BudgetRow.period)).scalars().all()
    assert first > 200 and again == 0
    assert latest <= NOW and earliest.astimezone(SEOUL).strftime("%Y-%m") == "2026-05"
    assert set(budgets) == {"2026-05"}  # 가장 이른 달에 두고 이어 쓴다
