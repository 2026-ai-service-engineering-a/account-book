from __future__ import annotations

from tests.api.conftest import FakeUnitOfWork, client_with
from tests.api.interfaces.schemas.test_run_write import run_body

KEY = {"Idempotency-Key": "run:0b6f0e4e-1c1e-4a51-9d2b-9a1f3c0d2e10"}


def test_records_a_run_with_its_tool_calls():
    uow = FakeUnitOfWork()
    response = client_with(uow=uow).post("/v1/runs", json=run_body(), headers=KEY)
    assert response.status_code == 201 and response.json() == {"id": run_body()["id"]}
    (run,) = uow.runs.rows.values()
    assert run.stop_reason == "answered" and run.tool_calls[0].tool == "summarize_spending"


def test_sending_it_again_with_the_same_key_keeps_one_row():
    uow = FakeUnitOfWork()
    client = client_with(uow=uow)
    first = client.post("/v1/runs", json=run_body(), headers=KEY)
    again = client.post("/v1/runs", json=run_body(), headers=KEY)
    assert first.status_code == again.status_code == 201 and len(uow.runs.rows) == 1


def test_missing_key_is_400_and_a_bad_body_is_422():
    client = client_with(uow=FakeUnitOfWork())
    assert client.post("/v1/runs", json=run_body()).status_code == 400
    bad = client.post("/v1/runs", json=run_body(seat="insights"), headers=KEY)
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"
