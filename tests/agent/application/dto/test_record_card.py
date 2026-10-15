from __future__ import annotations

from datetime import date

from agent.application.dto import RecordCard
from agent.domain.values import Direction


def test_nothing_unsure_by_default():
    card = RecordCard("r1", date(2026, 10, 14), "식비", Direction.EXPENSE, 8500, "카드", "김밥천국")
    assert card.unsure == ()
