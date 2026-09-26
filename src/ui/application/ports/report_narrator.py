from __future__ import annotations

from typing import Protocol

from ui.application.dto import BudgetStatus, MonthlyReport


class ReportNarrator(Protocol):
    """AI 자리 ③ — 리포트의 "눈에 띈 것" 두세 문장(reports.md 3.2).

    문장 생성은 에이전트 일이다. 지금은 규칙으로 문구를 고르는 대역이 선다.
    """

    async def narrate(
        self, report: MonthlyReport, budgets: tuple[BudgetStatus, ...]
    ) -> tuple[str, ...]: ...
