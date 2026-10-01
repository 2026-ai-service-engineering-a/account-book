from __future__ import annotations

from sqlalchemy import UniqueConstraint

from api.infrastructure.db import Base
from api.infrastructure.db.rows import BudgetRow


def test_maps_the_budgets_table():
    assert BudgetRow.__tablename__ == "budgets"


def test_one_budget_per_category_per_month():
    table = Base.metadata.tables[BudgetRow.__tablename__]
    unique = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert [sorted(col.name for col in u.columns) for u in unique] == [["category_id", "period"]]
