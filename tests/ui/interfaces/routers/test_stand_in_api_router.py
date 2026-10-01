from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.interfaces.web_app import build_web_app
from ui.main import create_app

MODEL = "gemini/gemini-embedding-001"


def test_suggest_returns_history_for_a_regular_place(client):
    body = client.post(
        "/v1/categories/suggest", json={"merchant": "김밥천국", "direction": "expense"}
    ).json()
    assert body["strategy"] == "history" and body["candidates"][0]["category_id"] == "food"
    assert {c["id"] for c in body["categories"]} >= {"food", "cafe"}
    assert isinstance(body["evidence"][0]["amount"], int)


def test_embedding_round_trip(client):
    pending = client.get("/v1/embeddings/pending", params={"model": MODEL}).json()["items"]
    assert pending and {"text_hash", "text"} <= set(pending[0])
    first = pending[0]["text_hash"]
    put = client.put(
        f"/v1/embeddings/{first}",
        json={"model": MODEL, "vector": [0.1, 0.2]},
        headers={"Idempotency-Key": f"emb:{first}"},
    )
    assert put.status_code == 204
    after = client.get("/v1/embeddings/pending", params={"model": MODEL}).json()["items"]
    assert first not in {i["text_hash"] for i in after}


def test_write_without_idempotency_key_is_400(client):
    put = client.put("/v1/embeddings/abc", json={"model": MODEL, "vector": [0.1]})
    assert put.status_code == 400 and put.json()["error"]["code"] == "idempotency_key_required"


def test_bad_body_is_422(client):
    assert client.post("/v1/categories/suggest", json={"direction": "sideways"}).status_code == 422


def test_not_mounted_without_an_index():
    app = create_app(clock=FixedClock(), seeded=False)
    services = dataclasses.replace(app.state.services, index=None)
    client = TestClient(build_web_app(services))
    response = client.post("/v1/categories/suggest", json={"direction": "expense"})
    assert response.status_code == 404
