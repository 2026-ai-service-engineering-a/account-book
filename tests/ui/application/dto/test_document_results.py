from __future__ import annotations

from ui.application.dto import DocumentResults, SearchMode


def test_did_not_fall_back_unless_told():
    assert not DocumentResults((), SearchMode.KEYWORD).fell_back
