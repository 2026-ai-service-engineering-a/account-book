from __future__ import annotations

from agent.domain.tools import Frequency
from agent.domain.values import Amount
from agent.infrastructure.http.frequency_reply import FrequencyReply


def test_nulls_stay_none():
    body = {"count": 1, "day_count": 1, "avg_gap_days": None, "avg_amount": 5200}
    assert FrequencyReply.model_validate(body).frequency() == Frequency(1, 1, None, Amount(5200))
    empty = {"count": 0, "day_count": 0, "avg_gap_days": None, "avg_amount": None}
    assert FrequencyReply.model_validate(empty).frequency().avg_amount is None
