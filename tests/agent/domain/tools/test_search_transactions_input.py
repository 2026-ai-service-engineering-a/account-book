from __future__ import annotations

import pytest

from agent.domain.tools import DEFAULT_ROWS, MAX_ROWS, SearchTransactionsInput
from agent.domain.values import PeriodName, PeriodSpec

WEEK = PeriodSpec(PeriodName.THIS_WEEK)


def test_twenty_rows_by_default():
    assert SearchTransactionsInput(WEEK).limit == DEFAULT_ROWS == 20


@pytest.mark.parametrize("limit", [0, MAX_ROWS + 1])
def test_limit_is_narrower_than_the_contract(limit):
    with pytest.raises(ValueError):
        SearchTransactionsInput(WEEK, limit=limit)
