from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from ui.interfaces.request_id import assign_request_id, request_id_of


def test_every_response_carries_an_id():
    app = FastAPI()
    app.middleware("http")(assign_request_id)

    @app.get("/")
    async def echo(request: Request) -> str:
        return request_id_of(request)

    client = TestClient(app)
    first, second = client.get("/"), client.get("/")
    assert first.json() == first.headers["X-Request-Id"]
    assert len(first.json()) == 16 and first.json() != second.json()
