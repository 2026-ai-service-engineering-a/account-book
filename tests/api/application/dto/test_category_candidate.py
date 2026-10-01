from __future__ import annotations

import pytest

from api.application.dto import CategoryCandidate
from api.domain.values import CategoryId


@pytest.mark.parametrize("bad", [-0.1, 1.01])
def test_confidence_is_between_zero_and_one(bad):
    with pytest.raises(ValueError):
        CategoryCandidate(CategoryId("cafe"), bad)
