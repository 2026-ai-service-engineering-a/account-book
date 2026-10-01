from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class Totals:
    """지출 합과 수입 합. 순액은 두지 않는다(ui-design 2.1)."""

    expense: Money
    income: Money
