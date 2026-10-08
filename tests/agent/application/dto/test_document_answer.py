from __future__ import annotations

from agent.application.dto import AnswerStatus, DocumentAnswer, Retrieval
from agent.domain.values import SearchMode


def test_carries_the_search_results_whatever_the_end():
    retrieval = Retrieval(SearchMode.HYBRID, False, ())
    answer = DocumentAnswer(
        AnswerStatus.SEARCH_ONLY, "", (), retrieval, "지금은 답을 만들 수 없어요."
    )
    assert answer.chunks == () and answer.reason
