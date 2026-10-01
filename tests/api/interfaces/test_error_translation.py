from __future__ import annotations

from tests.api.conftest import client_with


def test_unknown_id_is_404_not_found():
    body = client_with().get("/v1/transactions/nope").json()
    assert body["error"]["code"] == "not_found"


def test_malformed_body_is_422_with_field_details():
    response = client_with().post(
        "/v1/transactions", json={"amount": "8,500원"}, headers={"Idempotency-Key": "k"}
    )
    assert response.status_code == 422
    assert {"amount", "direction"} <= set(response.json()["error"]["details"])


def test_unexpected_errors_are_500_without_internals():
    class Broken:
        def __call__(self):
            raise RuntimeError("SELECT * FROM secrets")

    response = client_with(uow=Broken()).get("/v1/categories")
    assert response.status_code == 500 and "SELECT" not in response.text
    assert response.json()["error"]["code"] == "internal_error"
