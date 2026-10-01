from __future__ import annotations

import pytest

from agent.domain.values import Confidence


def test_orders_like_a_number():
    assert Confidence(0.3) < Confidence(0.7)


@pytest.mark.parametrize("bad", [-0.01, 1.01, 80, True])
def test_only_zero_to_one(bad):
    with pytest.raises(ValueError):
        Confidence(bad)
