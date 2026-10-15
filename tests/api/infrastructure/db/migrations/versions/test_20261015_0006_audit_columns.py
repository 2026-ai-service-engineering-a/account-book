from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration

RUN = (
    "INSERT INTO agent_runs (id, seat, flow, utterance, model, status, stop_reason) "
    "VALUES (:id, :seat, 'single', '', 'm', :status, 'read')"
)


def columns(database, table: str) -> set[str]:
    return {c["name"] for c in inspect(database).get_columns(table)}


def test_adds_the_columns_and_takes_them_back(database):
    migrate(database, "0006")
    assert {"seat", "flow", "stop_reason"} <= columns(database, "agent_runs")
    assert "call_id" in columns(database, "tool_calls")
    migrate(database, "0005", down=True)
    assert "seat" not in columns(database, "agent_runs")
    assert "call_id" not in columns(database, "tool_calls")


@pytest.mark.parametrize(("seat", "status"), [("insights", "done"), ("chat", "running")])
def test_seat_and_status_are_from_the_lists(database, seat, status):
    migrate(database, "0006")
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": seat, "status": status})


def test_a_call_id_is_unique_in_its_run(database):
    migrate(database, "0006")
    call = "INSERT INTO tool_calls (run_id, call_id, tool, args) VALUES ('r1', 'c1', 't', '{}')"
    with database.begin() as connection:
        connection.execute(text(RUN), {"id": "r1", "seat": "chat", "status": "done"})
        connection.execute(text(call))
    with pytest.raises(IntegrityError), database.begin() as connection:
        connection.execute(text(call))
