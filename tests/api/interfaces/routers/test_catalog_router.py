from __future__ import annotations

from tests.api.conftest import client_with


def test_categories_by_direction_and_accounts():
    client = client_with()
    assert [c["id"] for c in client.get("/v1/categories?direction=income").json()] == ["salary"]
    assert client.get("/v1/accounts").json() == [{"id": "card", "name": "카드", "kind": "card"}]
