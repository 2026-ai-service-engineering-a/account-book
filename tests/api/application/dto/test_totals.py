from __future__ import annotations

from api.application.dto import Totals
from api.domain.values import Money


def test_two_sums_no_net():
    totals = Totals(Money(1000), Money(3000))
    assert (totals.expense, totals.income) == (Money(1000), Money(3000))
    assert not hasattr(totals, "net")  # 순액은 두지 않는다
