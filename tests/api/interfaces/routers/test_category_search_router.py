from __future__ import annotations

import uuid

from api.domain.rules.searchable_text import text_hash
from tests.api.application.use_cases.test_suggest_category import ledger
from tests.api.conftest import client_with


def test_suggest_history_with_the_dictionary():
    body = (
        client_with(uow=ledger())
        .post("/v1/categories/suggest", json={"merchant": "김밥천국", "direction": "expense"})
        .json()
    )
    assert body["strategy"] == "history" and body["candidates"][0]["category_id"] == "food"
    assert {c["id"] for c in body["categories"]} == {"food", "cafe"}


def test_embedding_round_trip():
    uow = ledger()
    client = client_with(uow=uow)
    items = client.get("/v1/embeddings/pending", params={"model": "m@768"}).json()["items"]
    assert {i["text"] for i in items} == {"김밥천국", "스타벅스", "월급"}
    first = text_hash("스타벅스")
    put = client.put(
        f"/v1/embeddings/{first}",
        json={"model": "m@768", "vector": [0.1] * 768},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert put.status_code == 204 and uow.index.stored_vector("m@768", first) is not None


def test_wrong_dimension_is_422_and_missing_key_is_400():
    client = client_with(uow=ledger())
    bad = client.put(
        "/v1/embeddings/h", json={"model": "m", "vector": [0.1]}, headers={"Idempotency-Key": "k"}
    )
    assert bad.status_code == 422 and "vector" in bad.json()["error"]["details"]
    assert client.put("/v1/embeddings/h", json={"model": "m", "vector": [0.1]}).status_code == 400
