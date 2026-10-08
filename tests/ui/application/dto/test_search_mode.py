from __future__ import annotations

from ui.application.dto import SearchMode


def test_three_ways_with_labels_for_the_select():
    assert [m.value for m in SearchMode] == ["keyword", "vector", "hybrid"]
    assert SearchMode.HYBRID.label == "둘 다(하이브리드)"
