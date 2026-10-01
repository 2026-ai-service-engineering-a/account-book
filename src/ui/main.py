"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

api는 아직 없어서 메모리 대역이다. agent는 `AGENT_BASE_URL`이 있으면 진짜를 부르고, 없으면
각본 대역이 선다. 진짜가 생기면 이 파일에서 한 줄씩 바꾼다.

    uvicorn ui.main:create_app --factory
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

from fastapi import FastAPI

from ui.application.ports import CaptureReader, CategorySuggester, Clock
from ui.infrastructure.agent import AgentCaptureReader, AgentCategorySuggester
from ui.infrastructure.memory import (
    MemoryBudgetGateway,
    MemoryCatalogGateway,
    MemoryCategoryIndex,
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

# agent가 붙으면 진짜가 서는 자리(ai_map의 key)
_LIVE = frozenset({"capture", "classify"})


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
    # 채팅은 아직 각본 대역이라 각본 대역끼리 짝을 짓는다. 폼의 AI 버튼만 진짜 agent를 부른다.
    chat = ScriptedChatAgent(
        transactions,
        reports,
        budgets,
        catalog,
        ScriptedCategorySuggester(),
        clock,
        token_delay=token_delay,
    )
    return build_web_app(
        Services(
            transactions=transactions,
            reports=reports,
            budgets=budgets,
            catalog=catalog,
            suggester=_category_suggester(settings),
            chat=chat,
            narrator=ScriptedReportNarrator(),
            clock=clock,
            demo=MemoryDemoData(store, clock),
            capture=_capture_reader(settings, capture_delay),
            index=MemoryCategoryIndex(store, settings.rag_top_k, settings.rag_vote_temperature),
            live_seats=_LIVE if settings.agent_base_url else frozenset(),
        )
    )


def _capture_reader(settings: Settings, delay: float) -> CaptureReader:
    if not settings.agent_base_url:
        return ScriptedCaptureReader(delay=delay)
    # 값 뽑기와 카테고리 고르기가 LLM을 각각 한 번씩, 스키마를 못 맞추면 한 번씩 더 부른다.
    timeout = settings.agent_timeout_seconds * 4 + 2
    return AgentCaptureReader(settings.agent_base_url, settings.user_timezone, timeout)


def _category_suggester(settings: Settings) -> CategorySuggester:
    if not settings.agent_base_url:
        return ScriptedCategorySuggester()
    # 검색 → (애매하면) LLM 한 번. 스키마를 못 맞추면 한 번 더 부르는 것까지 기다린다.
    timeout = settings.agent_timeout_seconds * 2 + 2
    return AgentCategorySuggester(settings.agent_base_url, timeout)
