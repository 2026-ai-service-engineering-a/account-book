from __future__ import annotations

import pytest

from agent.domain.tools import SuggestCategoryInput
from agent.domain.values import Direction


def test_merchant_or_memo():
    assert SuggestCategoryInput("", memo="점심").direction is Direction.EXPENSE
    with pytest.raises(ValueError):
        SuggestCategoryInput("  ")
