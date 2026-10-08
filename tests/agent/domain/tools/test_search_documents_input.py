from __future__ import annotations

import pytest

from agent.domain.tools import SearchDocumentsInput
from agent.domain.tools.search_documents_input import QUERY_LIMIT


def test_a_query_is_one_sentence_within_the_api_limit():
    assert SearchDocumentsInput("할부 철회 기간").query == "할부 철회 기간"
    with pytest.raises(ValueError):
        SearchDocumentsInput("  ")
    with pytest.raises(ValueError):
        SearchDocumentsInput("가" * (QUERY_LIMIT + 1))
