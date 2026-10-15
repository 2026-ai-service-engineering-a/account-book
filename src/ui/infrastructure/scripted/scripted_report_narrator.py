from __future__ import annotations

from ui.application.dto import BudgetStatus, MonthlyReport, Period, ReportInsight

from .korean_josa import josa

_MAX_LINES = 3


class ScriptedReportNarrator:
    """키 없이 도는 대역. 큰 변화 두세 개를 규칙으로 골라 문장으로 낸다. 그림은 고르지 않는다.

    agent가 있으면 agent의 `POST /insights`가 대신 선다(AgentReportNarrator).
    """

    async def narrate(
        self, period: Period, report: MonthlyReport, budgets: tuple[BudgetStatus, ...]
    ) -> ReportInsight:
        lines: list[str] = []
        rises = sorted(
            (c for c in report.by_category if c.delta and c.delta.amount > 0),
            key=lambda c: c.delta.amount if c.delta else 0,
            reverse=True,
        )
        for change in rises[:2]:
            lines.append(
                f"{josa(change.category.name, '이', '가')} 지난달보다 {change.delta:,}원 늘었어요."
            )
        for status in budgets:
            if status.over_on is not None and len(lines) < _MAX_LINES:
                verb = "넘었어요" if status.is_over else "넘습니다"
                prefix = "" if status.is_over else "이 페이스면 "
                lines.append(
                    f"{status.category.name} — {prefix}{status.over_on.month}월 "
                    f"{status.over_on.day}일에 예산을 {verb}."
                )
        calm = [s for s in budgets if s.percent is not None and s.percent < 50]
        if calm and len(lines) < _MAX_LINES:
            lowest = min(calm, key=lambda s: s.percent or 0)
            lines.append(
                f"{josa(lowest.category.name, '은', '는')} 예산의 {lowest.percent}%만 썼어요."
            )
        return ReportInsight(highlights=tuple(lines[:_MAX_LINES]))
