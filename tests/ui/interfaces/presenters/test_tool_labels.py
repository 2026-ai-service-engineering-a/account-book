from __future__ import annotations

from ui.interfaces.presenters.tool_labels import progress_label


def test_known_and_unknown_tools():
    assert progress_label("search_transactions") == "거래를 찾는 중…"
    assert progress_label("mystery") == "생각하는 중…"
