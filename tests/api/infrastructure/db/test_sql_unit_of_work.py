from __future__ import annotations

import pytest

from api.application.dto import StoredReply
from api.application.ports import UnitOfWork
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration


def test_without_commit_everything_rolls_back(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    port: UnitOfWork = SqlUnitOfWork(sessions)
    with port as uow:
        uow.idempotency.claim("k1", "h1")
        uow.idempotency.complete("k1", StoredReply(201, {}))
    with SqlUnitOfWork(sessions) as uow:
        assert uow.idempotency.find("k1") is None


def test_commit_outside_the_block_is_a_bug(migrated):
    with pytest.raises(RuntimeError):
        SqlUnitOfWork(SqlUnitOfWork.factory(migrated)).commit()
