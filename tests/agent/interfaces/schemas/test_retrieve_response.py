from __future__ import annotations

from agent.application.dto import Retrieval
from agent.domain.values import SearchMode
from agent.interfaces.schemas import RetrieveResponse
from tests.agent.application.use_cases.test_retrieve import CHUNK


def test_says_the_mode_used_and_quotes_the_text():
    body = RetrieveResponse.of(Retrieval(SearchMode.KEYWORD, True, (CHUNK,))).model_dump(
        mode="json"
    )
    assert (body["mode"], body["fell_back"]) == ("keyword", True)
    assert body["chunks"][0]["effective_date"] == "2026-09-08"
