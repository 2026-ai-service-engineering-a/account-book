from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo
from typing import Annotated

from fastapi import Depends, Request

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
    ReportNarrator,
    TransactionGateway,
)


@dataclass(frozen=True, slots=True)
class Services:
    """라우터가 쓰는 포트 묶음. 무엇이 채우는지는 main.py만 안다."""

    transactions: TransactionGateway
    reports: ReportGateway
    budgets: BudgetGateway
    catalog: CatalogGateway
    documents: DocumentGateway
    answerer: DocumentAnswerer
    suggester: CategorySuggester
    chat: ChatAgent
    narrator: ReportNarrator
    clock: Clock
    demo: DemoData | None = None
    # AI를 끄면 None이다. 한 줄로 채우기 칸이 사라질 뿐 폼은 그대로 돈다.
    capture: CaptureReader | None = None
    # 각본 대역이 아니라 진짜 agent가 선 AI 자리(ai_map의 key). 위키가 "지금"을 말할 때 쓴다.
    live_seats: frozenset[str] = frozenset()
    # 문서 화면이 agent로 찾는가 — "AI 검색" 표시와 찾는 방법 고르기가 보인다
    documents_by_agent: bool = False

    def zone(self) -> tzinfo:
        """사용자 타임존. 시계가 aware를 내기로 했으니 없으면 조립이 잘못된 것이다."""
        zone = self.clock.now().tzinfo
        if zone is None:
            raise RuntimeError("Clock은 aware 시각을 내야 한다")
        return zone


def get_services(request: Request) -> Services:
    services = request.app.state.services
    if not isinstance(services, Services):
        raise RuntimeError("app.state.services가 조립되지 않았다")
    return services


ServicesDep = Annotated[Services, Depends(get_services)]
