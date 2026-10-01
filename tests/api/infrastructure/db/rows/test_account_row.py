from __future__ import annotations

from api.infrastructure.db.rows import AccountRow


def test_maps_the_accounts_table():
    assert AccountRow.__tablename__ == "accounts"
