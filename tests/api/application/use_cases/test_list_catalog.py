from __future__ import annotations

from api.application.use_cases import ListCatalog
from api.domain.values import Direction
from tests.api.conftest import FakeUnitOfWork


def test_categories_by_direction_and_accounts():
    catalog = ListCatalog(FakeUnitOfWork())
    assert [c.id for c in catalog.categories(Direction.INCOME)] == ["salary"]
    assert [a.id for a in catalog.accounts()] == ["card"]
