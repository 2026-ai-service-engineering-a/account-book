from __future__ import annotations

import pytest
from pydantic import ValidationError

from ui.application.dto import Direction
from ui.interfaces.stand_in_api import SuggestRequest


def test_becomes_a_query():
    query = SuggestRequest(direction="income", merchant="월급", query_vector=[0.1]).query()
    assert query.direction is Direction.INCOME and query.query_vector == (0.1,)


@pytest.mark.parametrize("broken", [{"direction": "out"}, {"query_vector": []}])
def test_rejects(broken):
    with pytest.raises(ValidationError):
        SuggestRequest.model_validate({"direction": "expense"} | broken)
