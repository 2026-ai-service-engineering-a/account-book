from __future__ import annotations

from agent.application.errors import LedgerUnavailable
from tests.agent.application.use_cases.test_retrieve import CHUNK
from tests.agent.conftest import FakeLedger, FakeModel
from tests.agent.interfaces.conftest import client_with


def test_returns_chunks_without_calling_a_generation_model():
    model = FakeModel()  # 대답을 하나도 준비하지 않았다 — 부르면 테스트가 깨진다
    ledger = FakeLedger(replies={"search_documents": (CHUNK,)})
    response = client_with(model, ledger).post("/retrieve", json={"q": "노트북 취소", "k": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "keyword" and body["chunks"][0]["title"] == "할부거래에 관한 법률"
    assert model.prompts == [] and model.tool_prompts == []


def test_api_down_is_503():
    ledger = FakeLedger(replies={"search_documents": LedgerUnavailable("ConnectError")})
    response = client_with(FakeModel(), ledger).post("/retrieve", json={"q": "노트북"})
    assert response.status_code == 503
