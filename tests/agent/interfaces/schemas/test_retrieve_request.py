from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.interfaces.schemas import RetrieveRequest


def test_left_out_means_the_agents_defaults():
    body = RetrieveRequest(q="노트북 취소")
    assert (body.k, body.strategy, body.mode) == (None, None, None)


@pytest.mark.parametrize("bad", [{"q": ""}, {"q": "x", "k": 0}, {"q": "x", "mode": "bm25"}])
def test_refuses_what_retrieval_cannot_do(bad):
    with pytest.raises(ValidationError):
        RetrieveRequest.model_validate(bad)
