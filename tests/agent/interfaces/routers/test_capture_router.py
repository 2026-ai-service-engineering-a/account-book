from __future__ import annotations

from agent.application.errors import ModelUnavailable
from tests.agent.conftest import SENTENCE, FakeModel, extraction
from tests.agent.interfaces.conftest import client_with

BODY = {"text": SENTENCE, "now": "2026-10-01T09:00:00+00:00", "timezone": "Asia/Seoul"}


def test_reads_with_the_users_reference_time():
    response = client_with(FakeModel(extraction())).post("/capture", json=BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == 5000 and body["merchant"] == "카페"
    assert body["occurred_at"] == "2026-10-01T15:00:00+09:00"


def test_refusal_is_still_200():
    # 못 읽은 것은 실패가 아니라 답이다. ui가 말풍선으로 옮긴다
    response = client_with(FakeModel(extraction(kind="question"))).post("/capture", json=BODY)
    assert response.status_code == 200 and response.json()["refusal"]


def test_unavailable_model_is_503_with_a_code():
    response = client_with(FakeModel(ModelUnavailable("x"))).post("/capture", json=BODY)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


def test_bad_body_is_422():
    response = client_with(FakeModel()).post("/capture", json=BODY | {"timezone": "Nowhere"})
    assert response.status_code == 422
