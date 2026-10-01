from __future__ import annotations

import pytest
from sqlalchemy import text

from api.application.dto import StoredReply
from api.application.errors import RequestInProgress
from api.application.ports import IdempotencyStore
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration


def test_claim_complete_find(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        port: IdempotencyStore = uow.idempotency
        port.claim("k1", "h1")
        found = port.find("k1")
        assert found is not None and found.reply is None  # 처리 중
        port.complete("k1", StoredReply(201, {"id": "t1"}))
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        found = uow.idempotency.find("k1")
        assert found is not None and found.reply == StoredReply(201, {"id": "t1"})


def test_second_claim_of_the_same_key_is_in_progress(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        uow.idempotency.claim("k1", "h1")
        uow.commit()
    with SqlUnitOfWork(sessions) as uow, pytest.raises(RequestInProgress):
        uow.idempotency.claim("k1", "h1")


def test_keys_older_than_a_day_are_forgotten(migrated):
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        uow.idempotency.claim("old", "h1")
        uow.idempotency.complete("old", StoredReply(204))
        uow.commit()
    with migrated.begin() as connection:
        connection.execute(
            text("UPDATE idempotency_keys SET created_at = now() - interval '25 hours'")
        )
    with SqlUnitOfWork(sessions) as uow:
        assert uow.idempotency.find("old") is None
