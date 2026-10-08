from __future__ import annotations

import pytest

from agent.domain.values import Amount


def test_sums_may_be_zero_and_changes_negative():
    assert Amount(0).amount == 0
    assert Amount(-47_200) == Amount(-47_200, "KRW")


@pytest.mark.parametrize("bad", [5000.0, True, "5000"])
def test_rejects_non_integers(bad):
    with pytest.raises(TypeError):
        Amount(bad)
