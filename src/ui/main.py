"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

api는 아직 없어서 메모리 대역이다. agent는 `AGENT_BASE_URL`이 있으면 진짜를 부르고, 없으면
각본 대역이 선다. 진짜가 생기면 이 파일에서 한 줄씩 바꾼다.

    uvicorn ui.main:create_app --factory
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

from fastapi import FastAPI

from ui.application.ports import CaptureReader, Clock
from ui.infrastructure.agent import AgentCaptureReader
from ui.infrastructure.memory import (
    MemoryBudgetGateway,
    MemoryCatalogGateway,
    MemoryDemoData,
    MemoryReportGateway,
    MemoryStore,
    MemoryTransactionGateway,
)
from ui.infrastructure.memory.demo_seed import seed_demo
from ui.infrastructure.scripted import (
    ScriptedCaptureReader,
    ScriptedCategorySuggester,
    ScriptedChatAgent,
    ScriptedReportNarrator,
)
from ui.infrastructure.settings import Settings
from ui.infrastructure.system_clock import SystemClock
from ui.interfaces.services import Services
from ui.interfaces.web_app import build_web_app


def create_app(
    settings: Settings | None = None,
    clock: Clock | None = None,
    seeded: bool = True,
    token_delay: float = 0.03,
    capture_delay: float = 0.4,
) -> FastAPI:
    settings = settings or Settings()
    zone = ZoneInfo(settings.user_timezone)
    clock = clock or SystemClock(zone)

    store = MemoryStore.create(zone)
    if seeded:
        seed_demo(store, clock.now())
    transactions = MemoryTransactionGateway(store)
    reports = MemoryReportGateway(store, clock)
    budgets = MemoryBudgetGateway(store, clock)
    catalog = MemoryCatalogGateway(store)
    suggester = ScriptedCategorySuggester()
    chat = ScriptedChatAgent(
        transactions, reports, budgets, catalog, suggester, clock, token_delay=token_delay
    )
    return build_web_app(
        Services(
            transactions=transactions,
            reports=reports,
            budgets=budgets,
            catalog=catalog,
            suggester=suggester,
            chat=chat,
            narrator=ScriptedReportNarrator(),
            clock=clock,
            demo=MemoryDemoData(store, clock),
            capture=_capture_reader(settings, capture_delay),
        )
    )


def _capture_reader(settings: Settings, delay: float) -> CaptureReader:
    if not settings.agent_base_url:
        return ScriptedCaptureReader(delay=delay)
    # agent는 스키마를 못 맞추면 LLM을 한 번 더 부른다. 그 두 번을 기다리고 조금 더 기다린다.
    timeout = settings.agent_timeout_seconds * 2 + 2
    return AgentCaptureReader(settings.agent_base_url, settings.user_timezone, timeout)
