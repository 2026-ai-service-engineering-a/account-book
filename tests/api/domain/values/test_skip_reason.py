from __future__ import annotations

from api.domain.values import SkipReason


def test_the_two_reasons_in_the_contract():
    assert {r.value for r in SkipReason} == {"short_history", "too_few"}
