from __future__ import annotations

from agent.domain.tools import SpendingTotals
from agent.domain.values import Amount


def test_two_sums_no_net():
    totals = SpendingTotals(Amount(0), Amount(3_000_000))
    assert totals.expense == Amount(0)
    assert not hasattr(totals, "net")
