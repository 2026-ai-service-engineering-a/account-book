from __future__ import annotations

from agent.application.dto import ChartPoint


def test_not_annotated_by_default():
    assert not ChartPoint("식비", 412000).annotated
