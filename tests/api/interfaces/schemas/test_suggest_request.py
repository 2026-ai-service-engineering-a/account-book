from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.domain.values import Direction
from api.interfaces.schemas import SuggestRequest


def test_becomes_a_query():
    query = SuggestRequest(direction="income", merchant="월급", query_vector=[0.1] * 768).query()
    assert query.direction is Direction.INCOME and len(query.query_vector or ()) == 768


@pytest.mark.parametrize("broken", [{"direction": "out"}, {"query_vector": [0.1, 0.2]}])
def test_rejects(broken):
    with pytest.raises(ValidationError):
        SuggestRequest.model_validate({"direction": "expense"} | broken)
