from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo
from typing import Annotated

from fastapi import Depends, Request

from ui.application.ports import (
    BudgetGateway,
    CatalogGateway,
    CategorySuggester,
    ChatAgent,
    Clock,
    DemoData,
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
    suggester: CategorySuggester
    chat: ChatAgent
    narrator: ReportNarrator
    clock: Clock
    demo: DemoData | None = None

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
