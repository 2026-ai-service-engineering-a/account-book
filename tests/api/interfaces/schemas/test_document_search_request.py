from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.interfaces.schemas import DocumentSearchRequest


def test_keyword_is_the_default_and_needs_no_vector():
    body = DocumentSearchRequest(q="카드")
    assert (body.mode, body.strategy, body.k, body.query_vector) == (
        "keyword",
        "paragraph",
        5,
        None,
    )


@pytest.mark.parametrize("bad", [{"q": ""}, {"q": "x", "k": 21}, {"q": "x", "mode": "bm25"}])
def test_refuses_what_the_search_cannot_do(bad):
    with pytest.raises(ValidationError):
        DocumentSearchRequest.model_validate(bad)
