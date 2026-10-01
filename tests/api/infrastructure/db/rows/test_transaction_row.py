from __future__ import annotations

from sqlalchemy import CheckConstraint, DateTime

from api.infrastructure.db import Base
from api.infrastructure.db.rows import TransactionRow

TABLE = Base.metadata.tables[TransactionRow.__tablename__]


def test_maps_the_transactions_table():
    assert TransactionRow.__tablename__ == "transactions"


def test_money_is_whole_won_and_time_is_aware():
    assert str(TABLE.c.amount.type) == "BIGINT"  # 정수 원. float가 아니다
    for column in (TABLE.c.occurred_at, TABLE.c.created_at):
        assert isinstance(column.type, DateTime) and column.type.timezone


def test_guards_what_the_schema_can_guard():
    names = " ".join(str(c.name) for c in TABLE.constraints if isinstance(c, CheckConstraint))
    assert all(name in names for name in ("amount_positive", "direction", "source"))
