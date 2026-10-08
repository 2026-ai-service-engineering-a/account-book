from __future__ import annotations

from agent.application.dto import Retrieval
from agent.domain.values import SearchMode


def test_says_what_it_actually_did():
    found = Retrieval(SearchMode.KEYWORD, True, ())
    assert found.fell_back and found.chunks == ()
