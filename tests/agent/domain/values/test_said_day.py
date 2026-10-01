from __future__ import annotations

from agent.domain.values import SaidDay


def test_names_the_model_chooses_from():
    assert SaidDay("day_before_yesterday") is SaidDay.DAY_BEFORE_YESTERDAY
    assert "date" in {d.value for d in SaidDay}
