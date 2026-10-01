from __future__ import annotations

import pytest

from agent.domain.values import Money


def test_holds_whole_won():
    assert Money(5000).amount == 5000


@pytest.mark.parametrize("bad", [5000.0, True, "5000"])
def test_rejects_non_integers(bad):
    with pytest.raises(TypeError):
        Money(bad)


@pytest.mark.parametrize("bad", [0, -1, 10_000_000_001])
def test_rejects_amounts_no_transaction_has(bad):
    with pytest.raises(ValueError):
        Money(bad)
