from __future__ import annotations

from agent.application.dto import AnswerStatus, DocumentAnswer, Retrieval
from agent.domain.values import SearchMode
from agent.interfaces.schemas import AskResponse
from tests.agent.application.use_cases.test_ask_documents import TRANSIT, WITHDRAW


def test_answer_with_citations_and_every_chunk():
    retrieval = Retrieval(SearchMode.HYBRID, False, (WITHDRAW, TRANSIT))
    found = DocumentAnswer(AnswerStatus.ANSWERED, "7일이에요.", (WITHDRAW,), retrieval)
    body = AskResponse.of(found).model_dump(mode="json")
    assert body["status"] == "answered" and [c["id"] for c in body["citations"]] == [WITHDRAW.id]
    assert len(body["chunks"]) == 2 and body["mode"] == "hybrid" and body["reason"] == ""
