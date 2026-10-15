from __future__ import annotations

from mcp_server.infrastructure.http.frequency_reply import FrequencyReply


def test_no_visits_have_no_average():
    reply = {"count": 0, "day_count": 0, "avg_gap_days": None, "avg_amount": None}
    assert FrequencyReply.model_validate(reply).row()["avg_amount"] is None
