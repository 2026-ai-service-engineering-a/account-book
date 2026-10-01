from __future__ import annotations

import pytest
from sqlalchemy import insert, select, update

from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.rows import AccountRow, CategoryRow

pytestmark = pytest.mark.integration


def test_seeding_twice_is_the_same_as_once(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
        seed_reference(connection)
        categories = connection.execute(select(CategoryRow.id)).scalars().all()
        accounts = connection.execute(select(AccountRow.id)).scalars().all()
    assert len(categories) == 8 and len(accounts) == 3


def test_fixes_names_and_leaves_user_categories_alone(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
        connection.execute(update(CategoryRow).where(CategoryRow.id == "cafe").values(name="커피"))
        pet = {"id": "pet", "name": "반려동물", "direction": "expense"}
        connection.execute(insert(CategoryRow).values(**pet))
        seed_reference(connection)
        names = dict(connection.execute(select(CategoryRow.id, CategoryRow.name)).all())
    assert names["cafe"] == "카페" and names["pet"] == "반려동물"
