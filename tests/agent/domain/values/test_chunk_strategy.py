from __future__ import annotations

from agent.domain.values import ChunkStrategy


def test_the_apis_three_strategies():
    assert {s.value for s in ChunkStrategy} == {"fixed_500", "paragraph", "paragraph_item"}
