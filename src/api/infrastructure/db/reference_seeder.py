from __future__ import annotations

from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from .reference_data import ACCOUNTS, CATEGORIES
from .rows import AccountRow, CategoryRow


def seed_reference(connection: Connection) -> int:
    """기준 데이터를 넣는다. 몇 번을 돌려도 같다 — 있으면 이름만 맞춘다. 넣은(맞춘) 행 수.

    사용자가 더한 카테고리는 건드리지 않는다. 지우지도 않는다.
    """
    categories = insert(CategoryRow).values(
        [
            {"id": i, "name": n, "direction": d, "position": p}
            for p, (i, n, d) in enumerate(CATEGORIES)
        ]
    )
    accounts = insert(AccountRow).values(
        [{"id": i, "name": n, "kind": k, "position": p} for p, (i, n, k) in enumerate(ACCOUNTS)]
    )
    connection.execute(
        categories.on_conflict_do_update(
            index_elements=[CategoryRow.id],
            set_={
                "name": categories.excluded.name,
                "direction": categories.excluded.direction,
                "position": categories.excluded.position,
            },
        )
    )
    connection.execute(
        accounts.on_conflict_do_update(
            index_elements=[AccountRow.id],
            set_={
                "name": accounts.excluded.name,
                "kind": accounts.excluded.kind,
                "position": accounts.excluded.position,
            },
        )
    )
    return len(CATEGORIES) + len(ACCOUNTS)
