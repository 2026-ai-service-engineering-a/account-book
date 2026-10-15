from __future__ import annotations

import pytest

from api.application.ports import InsightCache
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration
KEY = "a" * 64


def test_put_then_get_and_the_same_key_is_replaced(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        cache: InsightCache = uow.insight_cache
        assert cache.get(KEY) is None
        cache.put(KEY, {"charts": [], "highlights": ["첫째"]})
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        uow.insight_cache.put(KEY, {"charts": [], "highlights": ["둘째"]})
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        assert uow.insight_cache.get(KEY) == {"charts": [], "highlights": ["둘째"]}
