from __future__ import annotations

from typing import Protocol

from ui.application.dto import BudgetStatus, MonthlyReport, Period, ReportInsight


class ReportNarrator(Protocol):
    """AI 자리 ③ — 리포트의 "눈에 띈 것"(reports.md 3.2, docs/ai/agentic-reports.md).

    `AGENT_BASE_URL`이 있으면 agent의 `POST /insights`가 그림과 문장을 고르고, 없으면 규칙 문구를
    내는 대역이 선다. None은 "지금은 AI에 닿지 못했다"다 — 화면은 그 영역을 그리지 않는다.
    대역이 쓰는 리포트·예산을 같이 넘긴다. agent는 기간만 쓴다 — 숫자는 agent가 api에서 다시 읽는다.
    """

    async def narrate(
        self, period: Period, report: MonthlyReport, budgets: tuple[BudgetStatus, ...]
    ) -> ReportInsight | None: ...
