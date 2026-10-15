from __future__ import annotations

from agent.application.dto import Insight, InsightStop
from agent.interfaces.schemas import InsightResponse


def test_an_empty_answer_is_still_an_answer():
    body = InsightResponse.of(Insight(InsightStop.DISCARDED)).model_dump()
    assert body == {"charts": [], "highlights": []}
