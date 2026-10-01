from __future__ import annotations

from api.application.dto import Totals
from api.domain.values import Money
from api.interfaces.schemas import TotalsBody


def test_whole_won():
    assert TotalsBody.of(Totals(Money(1), Money(2))).model_dump() == {"expense": 1, "income": 2}
