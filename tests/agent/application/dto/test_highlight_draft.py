from __future__ import annotations

from agent.application.dto import HighlightDraft


def test_keeps_the_source_it_named():
    assert HighlightDraft("식비가 늘었어요.", "call_4").source == "call_4"
