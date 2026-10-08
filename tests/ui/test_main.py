from __future__ import annotations

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.infrastructure.agent import (
    AgentCaptureReader,
    AgentCategorySuggester,
    RoutedChatAgent,
)
from ui.infrastructure.api import (
    HttpBudgetGateway,
    HttpCatalogGateway,
    HttpReportGateway,
    HttpTransactionGateway,
)
from ui.infrastructure.scripted import ScriptedCaptureReader, ScriptedChatAgent
from ui.infrastructure.settings import Settings
from ui.main import create_app


def test_assembles_stand_ins_everywhere():
    services = create_app(clock=FixedClock(), seeded=False).state.services
    assert services.demo is not None  # 대역 모드에서는 대역 버튼이 켜져 있다
    assert isinstance(services.capture, ScriptedCaptureReader)


def test_agent_address_brings_the_real_reader():
    settings = Settings(_env_file=None, agent_base_url="http://agent:8001")
    services = create_app(settings, clock=FixedClock(), seeded=False).state.services
    assert isinstance(services.capture, AgentCaptureReader)
    assert isinstance(services.suggester, AgentCategorySuggester)
    assert isinstance(services.chat, RoutedChatAgent)  # 질문만 agent로, 기록은 대역으로
    assert services.live_seats == {"capture", "classify", "query"}


def test_api_address_brings_the_http_gateways_and_hides_the_demo_buttons():
    settings = Settings(_env_file=None, api_base_url="http://api:8000")
    services = create_app(settings, clock=FixedClock()).state.services
    assert isinstance(services.transactions, HttpTransactionGateway)
    assert isinstance(services.reports, HttpReportGateway)
    assert isinstance(services.budgets, HttpBudgetGateway)
    assert isinstance(services.catalog, HttpCatalogGateway)
    assert services.demo is None  # 쓰던 가계부를 비우는 버튼은 두지 않는다


def test_ui_no_longer_opens_v1():
    # 카테고리 검색은 api가 한다 — ui의 공개 포트에 /v1 대역이 없다
    client = TestClient(create_app(clock=FixedClock(), seeded=False))
    assert client.post("/v1/categories/suggest", json={"direction": "expense"}).status_code == 404


def test_seeded_flag_decides_first_screen():
    seeded = TestClient(create_app(clock=FixedClock(), seeded=True)).get("/transactions")
    empty = TestClient(create_app(clock=FixedClock(), seeded=False)).get("/transactions")
    assert "아직 기록이 없어요" not in seeded.text
    assert "아직 기록이 없어요" in empty.text


def test_without_an_agent_the_chat_is_the_scripted_stand_in():
    services = create_app(Settings(_env_file=None), clock=FixedClock(), seeded=False).state.services
    assert isinstance(services.chat, ScriptedChatAgent)
