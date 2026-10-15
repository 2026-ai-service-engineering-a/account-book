from __future__ import annotations

from agent.application.dto import ChartPoint
from agent.interfaces.schemas import ChartPointBody


def test_a_point_as_json():
    body = ChartPointBody.of(ChartPoint("생활", 1050000, True))
    assert body.model_dump() == {"label": "생활", "value": 1050000, "annotated": True}
