from __future__ import annotations

from api.infrastructure.db.rows import CategoryRow


def test_maps_the_categories_table():
    assert CategoryRow.__tablename__ == "categories"
