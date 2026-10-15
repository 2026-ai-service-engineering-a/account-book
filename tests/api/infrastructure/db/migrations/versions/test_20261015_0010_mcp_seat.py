from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

RUN = (
    "INSERT INTO agent_runs (id, seat, flow, utterance, model, status, stop_reason, client) "
    "VALUES (:id, :seat, :flow, '', 'external', 'done', 'answered', 'Claude Desktop')"
)


def test_an_mcp_call_is_recorded_after_0010_and_not_before(database):
    migrate(database, "0009")
    # 0010 전에는 client 칸이 없다
    with pytest.raises(ProgrammingError), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": "mcp", "flow": "direct"})
    migrate(database, "0010")
    with database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": "mcp", "flow": "direct"})
    for seat, flow in (("mcp", "loop"), ("outside", "direct")):
        with pytest.raises(IntegrityError), database.begin() as connection:
            connection.execute(text(RUN), {"id": "r2", "seat": seat, "flow": flow})
