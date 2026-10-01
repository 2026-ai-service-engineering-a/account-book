"""첫 마이그레이션을 실제 Postgres(pgvector)에 올리고 내린다."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError

from api.infrastructure.db import Base
from api.infrastructure.db.reference_seeder import seed_reference
from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

TABLES = {
    "accounts",
    "agent_runs",
    "budgets",
    "categories",
    "category_rules",
    "idempotency_keys",
    "text_embeddings",
    "tool_calls",
    "transactions",
}


def test_creates_every_table_and_turns_pgvector_on(migrated: Engine):
    assert set(inspect(migrated).get_table_names()) >= TABLES
    with migrated.connect() as connection:
        version = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
    assert version is not None


def test_migration_and_mappings_say_the_same_thing(migrated: Engine):
    # 매핑을 고치고 마이그레이션을 안 만들면 여기서 걸린다
    with migrated.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []


def test_hnsw_cosine_index_is_there(migrated: Engine):
    with migrated.connect() as connection:
        definition: str = connection.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_text_embeddings_vector'")
        ).scalar_one()
    assert "USING hnsw" in definition and "vector_cosine_ops" in definition


def test_nearest_neighbours_by_cosine_distance(migrated: Engine):
    """카테고리 고르기가 쓸 질의. 가장 가까운 텍스트가 먼저 온다."""

    def unit(i: int) -> str:
        return "[" + ",".join("1" if j == i else "0" for j in range(768)) + "]"

    cafe_ish = "[0.9,0.1" + ",0" * 766 + "]"
    rows = [("스타벅스", unit(0)), ("김밥천국", unit(1)), ("지하철", unit(2))]
    with migrated.begin() as connection:
        for name, vector in rows:
            connection.execute(
                text("INSERT INTO text_embeddings (model, text_hash, vector) VALUES ('m', :h, :v)"),
                {"h": name, "v": vector},
            )
        nearest = connection.execute(
            text(
                "SELECT text_hash, 1 - (vector <=> CAST(:q AS vector)) AS similarity "
                "FROM text_embeddings WHERE model = 'm' "
                "ORDER BY vector <=> CAST(:q AS vector) LIMIT 2"
            ),
            {"q": cafe_ish},
        ).all()
    assert [n.text_hash for n in nearest] == ["스타벅스", "김밥천국"]
    assert nearest[0].similarity > 0.99


def test_vector_dimension_is_enforced(migrated: Engine):
    with pytest.raises(Exception, match="768"), migrated.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO text_embeddings (model, text_hash, vector) VALUES ('m', 'h', '[1,2]')"
            )
        )


def test_amount_must_be_positive(migrated: Engine):
    with migrated.begin() as connection:
        seed_reference(connection)
    with pytest.raises(IntegrityError, match="amount_positive"), migrated.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO transactions (id, occurred_at, amount, direction, account_id, "
                "category_id, source) VALUES ('t1', :at, 0, 'expense', 'card', 'food', 'manual')"
            ),
            {"at": datetime(2026, 10, 1, tzinfo=UTC)},
        )


def test_down_and_up_again(migrated: Engine):
    migrate(migrated, "base", down=True)
    assert not TABLES & set(inspect(migrated).get_table_names())
    migrate(migrated)
    assert set(inspect(migrated).get_table_names()) >= TABLES
