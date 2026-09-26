from __future__ import annotations

from ui.application.dto import Source


def test_values_match_the_api_contract():
    # README 6장: 모든 거래에 manual / agent(/ import)가 박힌다
    assert {s.value for s in Source} == {"manual", "agent"}
