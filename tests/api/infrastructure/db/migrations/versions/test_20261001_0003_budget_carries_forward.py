from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from api.infrastructure.db.reference_seeder import seed_reference
from tests.api.conftest import migrate

pytestmark = pytest.mark.integration


def test_empty_limit_means_no_budget_and_zero_is_still_refused(database):
    migrate(database, "0003")
    with database.begin() as connection:
        seed_reference(connection)
        connection.execute(
            text("INSERT INTO budgets (category_id, period) VALUES ('food', '2026-09')")
        )
    with pytest.raises(IntegrityError, match="limit_positive"), database.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO budgets (category_id, period, limit_amount) "
                "VALUES ('cafe', '2026-09', 0)"
            )
        )


def test_down_drops_the_no_budget_rows(database):
    migrate(database, "0003")
    with database.begin() as connection:
        seed_reference(connection)
        connection.execute(
            text("INSERT INTO budgets (category_id, period) VALUES ('food', '2026-09')")
        )
    migrate(database, "0002", down=True)
    with database.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM budgets")).scalar() == 0
    columns = {c["name"]: c for c in inspect(database).get_columns("budgets")}
    assert columns["limit_amount"]["nullable"] is False
