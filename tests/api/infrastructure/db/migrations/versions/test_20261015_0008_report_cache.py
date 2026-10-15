from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from api.infrastructure.db.reference_seeder import seed_reference
from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

TX = (
    "INSERT INTO transactions (id, direction, amount, occurred_at, category_id, account_id, "
    "merchant, memo, source, search_text, text_hash, created_at) VALUES ('t1', 'expense', 1000, "
    "'2026-09-01T00:00:00Z', 'food', 'card', '', '', 'manual', '', 'h', '2026-09-02T00:00:00Z')"
)


def test_old_transactions_take_their_created_at_and_it_goes_back(database):
    migrate(database, "0007")
    with database.begin() as connection:
        seed_reference(connection)
        connection.execute(text(TX))
    migrate(database, "0008")
    with database.connect() as connection:
        updated = connection.execute(
            text("SELECT updated_at = created_at FROM transactions")
        ).scalar_one()
    assert updated  # 마이그레이션 시각으로 채우면 아무것도 안 바뀌었는데 바뀐 것처럼 보인다
    assert "insight_cache" in inspect(database).get_table_names()
    migrate(database, "0007", down=True)
    assert "insight_cache" not in inspect(database).get_table_names()
    columns = {c["name"] for c in inspect(database).get_columns("transactions")}
    assert "updated_at" not in columns
