"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

`API_BASE_URL`이 있으면 거래·카탈로그·집계·예산을 그 주소의 api가 하고, 없으면 메모리 대역이
선다. `AGENT_BASE_URL`이 있으면 AI 자리(한 줄로 채우기, 카테고리 고르기)에 진짜 agent가, 없으면
각본 대역이 선다. 둘은 따로 고른다 — 다만 카테고리 고르기는 agent가 api를 찾아보므로 api가 있어야
근거를 찾는다.

    uvicorn ui.main:create_app --factory
"""

from __future__ import annotations

from zoneinfo import ZoneInfo

from fastapi import FastAPI

from ui.application.ports import (
    BudgetGateway,
    CaptureReader,
    CatalogGateway,
    CategorySuggester,
    ChatAgent,
    Clock,
    DemoData,
    DocumentAnswerer,
    DocumentGateway,
    ReportGateway,
    TransactionGateway,
)
from ui.infrastructure.agent import (
    AgentCaptureReader,
    AgentCategorySuggester,
    AgentChatAgent,
    AgentDocumentAnswerer,
    AgentDocumentGateway,
    RoutedChatAgent,
)
from ui.infrastructure.api import (
    ApiClient,
    HttpBudgetGateway,
    HttpCatalogGateway,
    HttpDocumentGateway,
    HttpReportGateway,
    HttpTransactionGateway,
)
from ui.infrastructure.memory import (
    MemoryBudgetGateway,
    MemoryCatalogGateway,
    MemoryDemoData,
    MemoryDocumentGateway,
    MemoryReportGateway,
    MemoryStore,
    MemoryTransactionGateway,
)
from ui.infrastructure.memory.demo_seed import seed_demo
from ui.infrastructure.scripted import (
    ScriptedCaptureReader,
    ScriptedCategorySuggester,
    ScriptedChatAgent,
    ScriptedDocumentAnswerer,
    ScriptedReportNarrator,
)
from ui.infrastructure.settings import Settings
from ui.infrastructure.system_clock import SystemClock
from ui.interfaces.services import Services
from ui.interfaces.web_app import build_web_app

# agent가 붙으면 진짜가 서는 자리(ai_map의 key)
_LIVE = frozenset({"capture", "classify", "query"})
# api 호출 하나의 상한. 화면 한 장이 기다리는 시간이라 짧게 둔다 — 집계도 DB가 하니 금방이다.
_API_TIMEOUT = 5.0


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
    ledger = _api_ledger(settings) if settings.api_base_url else _memory_ledger(zone, clock, seeded)
    transactions, reports, budgets, catalog, demo = ledger
    # 채팅의 기록 쪽은 아직 각본 대역이다. 질문 쪽만 agent가 있으면 agent가 받는다.
    scripted = ScriptedChatAgent(
        transactions,
        reports,
        budgets,
        catalog,
        ScriptedCategorySuggester(),
        clock,
        token_delay=token_delay,
    )
    chat = _chat_agent(settings, clock, scripted)
    documents = _documents(settings)
    return build_web_app(
        Services(
            transactions=transactions,
            reports=reports,
            budgets=budgets,
            catalog=catalog,
            documents=documents,
            answerer=_answerer(settings, documents),
            suggester=_category_suggester(settings),
            chat=chat,
            narrator=ScriptedReportNarrator(),
            clock=clock,
            demo=demo,
            capture=_capture_reader(settings, capture_delay),
            live_seats=_LIVE if settings.agent_base_url else frozenset(),
            documents_by_agent=bool(settings.agent_base_url),
        )
    )


type _Ledger = tuple[
    TransactionGateway, ReportGateway, BudgetGateway, CatalogGateway, DemoData | None
]


def _api_ledger(settings: Settings) -> _Ledger:
    """진짜 api. 기록은 DB에 남는다. 데모 버튼은 없다 — 쓰던 가계부를 비우는 버튼을 두지 않는다."""
    client = ApiClient(settings.api_base_url, timeout=_API_TIMEOUT)
    return (
        HttpTransactionGateway(client),
        HttpReportGateway(client),
        HttpBudgetGateway(client),
        HttpCatalogGateway(client),
        None,
    )


def _memory_ledger(zone: ZoneInfo, clock: Clock, seeded: bool) -> _Ledger:
    """api 자리의 메모리 대역. 테스트와, api 없이 화면만 볼 때. 서버를 끄면 기록이 사라진다."""
    store = MemoryStore.create(zone)
    if seeded:
        seed_demo(store, clock.now())
    return (
        MemoryTransactionGateway(store),
        MemoryReportGateway(store, clock),
        MemoryBudgetGateway(store, clock),
        MemoryCatalogGateway(store),
        MemoryDemoData(store, clock),
    )


def _documents(settings: Settings) -> DocumentGateway:
    """문서 검색. api가 없으면 조문 네 줄짜리 대역이, agent가 있으면 agent의 /retrieve가 선다.

    agent가 죽으면 낱말 검색(api나 대역)으로 물러선다.
    """
    keyword: DocumentGateway = (
        HttpDocumentGateway(ApiClient(settings.api_base_url, timeout=_API_TIMEOUT))
        if settings.api_base_url
        else MemoryDocumentGateway()
    )
    if not settings.agent_base_url:
        return keyword
    # 처음 한 번은 색인 안 된 조각을 임베딩하느라 길다(조각 이백여 개, 묶음 셋)
    timeout = settings.agent_timeout_seconds * 3 + 2
    return AgentDocumentGateway(settings.agent_base_url, timeout, keyword)


def _answerer(settings: Settings, documents: DocumentGateway) -> DocumentAnswerer:
    """문서 Q&A. agent가 없으면 찾은 조문만 보이는 각본 대역이, 있으면 agent의 /ask가 선다."""
    scripted = ScriptedDocumentAnswerer(documents)
    if not settings.agent_base_url:
        return scripted
    # 찾기(임베딩) 한 번과 생성 한 번. 처음 한 번은 색인 안 된 조각까지 임베딩한다
    timeout = settings.agent_timeout_seconds * 4 + 2
    return AgentDocumentAnswerer(settings.agent_base_url, timeout, scripted)


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


def _chat_agent(settings: Settings, clock: Clock, scripted: ChatAgent) -> ChatAgent:
    if not settings.agent_base_url:
        return scripted
    # 이벤트 사이 한 번의 읽기 상한. 도구 고르기 LLM 한 번과 스키마 재시도까지 기다린다.
    # 실행 전체는 agent가 벽시계(대화 20초)로 끊는다.
    timeout = settings.agent_timeout_seconds * 2 + 2
    questions = AgentChatAgent(settings.agent_base_url, settings.user_timezone, clock, timeout)
    return RoutedChatAgent(questions, scripted)
