from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.application.dto import Chart, ChartPoint
from agent.interfaces.schemas import ChartBody


def test_a_chart_as_json():
    body = ChartBody.of(Chart("hbar", "9월", "KRW", (ChartPoint("식비", 412000),), "한 줄"))
    assert body.model_dump()["points"] == [{"label": "식비", "value": 412000, "annotated": False}]


def test_only_the_kinds_the_renderer_draws():
    with pytest.raises(ValidationError):
        ChartBody.of(Chart("pie", "9월", "KRW", ()))
