from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

RUN = (
    "INSERT INTO agent_runs (id, seat, flow, utterance, model, status, stop_reason) "
    "VALUES (:id, :seat, 'plan_execute', '', 'm', 'done', 'assembled')"
)


def test_insight_is_a_seat_after_0007_and_not_before(database):
    migrate(database, "0006")
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": "insight"})
    migrate(database, "0007")
    with database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": "insight"})
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r2", "seat": "insights"})
