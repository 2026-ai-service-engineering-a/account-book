from __future__ import annotations

from ui.application.dto import InsightPoint


def test_not_annotated_by_default():
    assert not InsightPoint("식비", 412000).annotated
