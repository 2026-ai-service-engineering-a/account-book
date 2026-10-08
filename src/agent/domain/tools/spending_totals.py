from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Amount


@dataclass(frozen=True, slots=True)
class SpendingTotals:
    """summarize_spending의 답. 순액은 두지 않는다(ui-design 2.1)."""

    expense: Amount
    income: Amount
