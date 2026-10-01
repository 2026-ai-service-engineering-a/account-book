from __future__ import annotations

from api.domain.values import AccountId


def test_is_a_str_at_runtime():
    assert AccountId("card") == "card"
