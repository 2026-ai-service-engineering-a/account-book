from __future__ import annotations

from ui.application.dto import AnswerStatus


def test_three_ways_to_end():
    assert [s.value for s in AnswerStatus] == ["answered", "abstained", "search_only"]
