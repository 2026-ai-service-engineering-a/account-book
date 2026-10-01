from __future__ import annotations

import uuid

import pytest

from api.infrastructure.db import SqlDatabaseProbe
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from tests.api.conftest import client_with
from tests.api.interfaces.test_write_headers import BODY


def key() -> dict[str, str]:
    return {"Idempotency-Key": str(uuid.uuid4()), "X-Confirmed-By": "user"}


def test_create_replays_with_the_same_key():
    client, headers = client_with(), key()
    first = client.post("/v1/transactions", json=BODY, headers=headers)
    again = client.post("/v1/transactions", json=BODY, headers=headers)
    assert first.status_code == again.status_code == 201
    assert first.json()["id"] == again.json()["id"]
    reused = client.post("/v1/transactions", json=BODY | {"amount": 1}, headers=headers)
    assert reused.json()["error"]["code"] == "idempotency_key_reused"


def test_write_without_a_key_is_400():
    response = client_with().post("/v1/transactions", json=BODY)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_validation_details_reach_the_field():
    response = client_with().post(
        "/v1/transactions", json=BODY | {"category_id": "salary"}, headers=key()
    )
    assert response.status_code == 422
    assert response.json()["error"]["details"] == {
        "category_id": "방향에 맞는 카테고리가 아닙니다."
    }


def test_big_amount_without_confirmation_is_412():
    headers = {"Idempotency-Key": "k"}
    response = client_with().post(
        "/v1/transactions", json=BODY | {"amount": 500_000}, headers=headers
    )
    assert response.status_code == 412
    assert response.json()["error"]["code"] == "confirmation_required"


def test_agent_run_id_marks_the_source():
    headers = key() | {"X-Agent-Run-Id": "run-1"}
    assert (
        client_with().post("/v1/transactions", json=BODY, headers=headers).json()["source"]
        == "agent"
    )


def test_update_and_delete():
    client = client_with()
    created = client.post("/v1/transactions", json=BODY, headers=key()).json()
    path = f"/v1/transactions/{created['id']}"
    assert client.patch(path, json=BODY | {"amount": 9000}, headers=key()).json()["amount"] == 9000
    assert client.delete(path, headers={"Idempotency-Key": "d1"}).status_code == 412
    assert client.delete(path, headers=key()).status_code == 204
    assert client.get(path).status_code == 404


def test_bad_query_is_422():
    assert client_with().get("/v1/transactions?period=2026-13").status_code == 422


@pytest.mark.integration
def test_end_to_end_on_a_real_database(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    sessions = SqlUnitOfWork.factory(migrated)
    client = client_with(uow=lambda: SqlUnitOfWork(sessions), database=SqlDatabaseProbe(migrated))
    assert client.get("/v1/healthz").json() == {"status": "ok"}
    created = client.post("/v1/transactions", json=BODY, headers=key()).json()
    page = client.get("/v1/transactions?period=2026-09").json()
    assert [t["id"] for t in page["items"]] == [created["id"]]
    assert client.get("/v1/transactions?period=2026-10").json()["items"] == []
