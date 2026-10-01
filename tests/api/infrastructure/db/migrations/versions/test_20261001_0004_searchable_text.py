from __future__ import annotations

import pytest
from sqlalchemy import text

from api.infrastructure.db.reference_seeder import seed_reference
from tests.api.conftest import migrate

pytestmark = pytest.mark.integration


def test_fills_existing_transactions(database):
    migrate(database, "0003")
    with database.begin() as connection:
        seed_reference(connection)
        connection.execute(
            text(
                "INSERT INTO transactions (id, occurred_at, amount, direction, account_id, "
                "category_id, merchant, memo, source) VALUES "
                "('t1', now(), 1000, 'expense', 'card', 'food', "
                "'(주)김밥천국 강남점', '점심', 'manual')"
            )
        )
    migrate(database, "0004")
    with database.connect() as connection:
        row = connection.execute(text("SELECT search_text, text_hash FROM transactions")).one()
    assert row.search_text == "김밥천국 점심" and len(row.text_hash) == 16
    migrate(database, "0003", down=True)
