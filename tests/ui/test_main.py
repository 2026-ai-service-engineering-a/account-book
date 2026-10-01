from __future__ import annotations

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.infrastructure.agent import AgentCaptureReader
from ui.infrastructure.scripted import ScriptedCaptureReader
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
    assert services.live_seats == {"capture"}


def test_seeded_flag_decides_first_screen():
    seeded = TestClient(create_app(clock=FixedClock(), seeded=True)).get("/transactions")
    empty = TestClient(create_app(clock=FixedClock(), seeded=False)).get("/transactions")
    assert "아직 기록이 없어요" not in seeded.text
    assert "아직 기록이 없어요" in empty.text
