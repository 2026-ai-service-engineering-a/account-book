from __future__ import annotations

from tests.api.conftest import FakeUnitOfWork, client_with

KEY = "b" * 64
BODY = {"body": {"charts": [], "highlights": ["생활이 늘었어요."]}}


def test_a_miss_then_a_put_then_a_hit():
    client = client_with(uow=FakeUnitOfWork())
    assert client.get(f"/v1/insights/cache/{KEY}").json() == {"key": KEY, "body": None}
    put = client.put(f"/v1/insights/cache/{KEY}", json=BODY, headers={"Idempotency-Key": "c1"})
    assert put.status_code == 204
    assert client.get(f"/v1/insights/cache/{KEY}").json()["body"] == BODY["body"]


def test_only_a_sha256_key_and_writes_need_a_key():
    client = client_with(uow=FakeUnitOfWork())
    assert client.get("/v1/insights/cache/../etc").status_code == 404
    assert client.get("/v1/insights/cache/xyz").status_code == 422
    assert client.put(f"/v1/insights/cache/{KEY}", json=BODY).status_code == 400
