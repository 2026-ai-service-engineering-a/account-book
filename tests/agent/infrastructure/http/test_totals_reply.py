from __future__ import annotations

from agent.domain.tools import SpendingTotals
from agent.domain.values import Amount
from agent.infrastructure.http.totals_reply import TotalsReply


def test_two_sums():
    reply = TotalsReply.model_validate({"expense": 0, "income": 3_200_000})
    assert reply.totals() == SpendingTotals(Amount(0), Amount(3_200_000))
