from __future__ import annotations

import pytest

from api.application.ports import CatalogRepository
from api.domain.values import Direction
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration


def test_in_display_order(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    with SqlUnitOfWork(SqlUnitOfWork.factory(migrated)) as uow:
        port: CatalogRepository = uow.catalog
        expense = [c.name for c in port.categories(Direction.EXPENSE)]
        accounts = [a.id for a in port.accounts()]
    assert expense == ["식비", "카페", "교통", "생활", "주거", "기타"]  # 이름순이 아니다
    assert accounts == ["card", "cash", "bank"]
