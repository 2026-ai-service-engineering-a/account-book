from __future__ import annotations

from agent.application.errors import ModelUnavailable
from tests.agent.application.use_cases.test_ask_documents import TRANSIT, WITHDRAW, reply
from tests.agent.conftest import FakeLedger, FakeModel
from tests.agent.interfaces.conftest import client_with


def ledger() -> FakeLedger:
    return FakeLedger(replies={"search_documents": (WITHDRAW, TRANSIT)})


def test_a_cited_answer():
    model = FakeModel(reply("계약서를 받은 날부터 7일 안에 철회할 수 있어요.", ("c1",)))
    body = client_with(model, ledger()).post("/ask", json={"q": "노트북 취소"}).json()
    assert body["status"] == "answered" and body["citations"][0]["title"] == "할부거래에 관한 법률"
    assert model.tool_prompts == []  # 도구 호출은 쓰지 않는다


def test_a_model_outage_is_still_200_with_the_search_results():
    response = client_with(FakeModel(ModelUnavailable("down")), ledger()).post(
        "/ask", json={"q": "노트북 취소"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "search_only" and len(body["chunks"]) == 2 and body["answer"] == ""
