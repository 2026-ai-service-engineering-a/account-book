from __future__ import annotations

import pytest

from ui.application.errors import TransactionNotFound


def test_carries_the_missing_id():
    with pytest.raises(TransactionNotFound) as caught:
        raise TransactionNotFound("t99999")
    assert str(caught.value) == "t99999"
