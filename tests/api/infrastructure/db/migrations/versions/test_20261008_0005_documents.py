from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration


def test_turns_on_pg_trgm_and_makes_the_two_tables(database):
    migrate(database, "0005")
    assert {"documents", "document_chunks"} <= set(inspect(database).get_table_names())
    with database.connect() as connection:
        assert connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm'")
        ).scalar()
        definition = connection.execute(
            text(
                "SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_document_chunks_search_text'"
            )
        ).scalar_one()
    assert "USING gin" in definition and "gin_trgm_ops" in definition
    migrate(database, "0004", down=True)
    assert "documents" not in inspect(database).get_table_names()


def test_strategy_is_one_of_three(database):
    migrate(database, "0005")
    with database.begin() as connection:
        connection.execute(
            text("INSERT INTO documents VALUES ('법', '법', '출처', '1', '2026-10-01', '본문')")
        )
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO document_chunks VALUES "
                "('x:법/1', '법', 'whole_doc', '제1조', '본문', '본문', 'h', 1)"
            )
        )
