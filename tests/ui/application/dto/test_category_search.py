from __future__ import annotations

from ui.application.dto import CategorySearch, SearchStrategy


def test_empty_search():
    search = CategorySearch(SearchStrategy.NONE, "", False, (), (), ())
    assert not search.candidates and not search.evidence
