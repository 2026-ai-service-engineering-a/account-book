from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DataError, IntegrityError

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

RUN = (
    "INSERT INTO agent_runs (id, seat, flow, utterance, model, status, stop_reason) "
    "VALUES (:id, 'capture', 'single', '', 'm', :status, 'proposed')"
)


def test_a_proposal_may_wait_after_0009_and_not_before(database):
    migrate(database, "0008")
    # 0009 전에는 칸 길이(20자)에 먼저 걸리고, 그게 아니어도 CHECK에 걸린다
    with pytest.raises((DataError, IntegrityError)), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "status": "awaiting_confirmation"})
    migrate(database, "0009")
    with database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "status": "awaiting_confirmation"})
        connection.execute(text(RUN), {"id": "r2", "status": "aborted"})
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r3", "status": "running"})
