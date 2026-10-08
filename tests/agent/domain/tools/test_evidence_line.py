from __future__ import annotations

from datetime import date

from agent.domain.tools import EvidenceLine
from agent.domain.values import Amount, CategoryId


def test_a_past_transaction():
    line = EvidenceLine("김밥천국", "", CategoryId("food"), Amount(8_500), date(2026, 9, 16))
    assert line.day == date(2026, 9, 16)
