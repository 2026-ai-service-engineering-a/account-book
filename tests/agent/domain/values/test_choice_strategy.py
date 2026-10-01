from __future__ import annotations

from agent.domain.values import ChoiceStrategy


def test_llm_is_its_own_path():
    assert {s.value for s in ChoiceStrategy} == {"rule", "history", "vector", "llm", "none"}
