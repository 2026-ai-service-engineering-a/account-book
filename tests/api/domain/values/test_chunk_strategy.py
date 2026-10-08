from __future__ import annotations

from api.domain.values import ChunkStrategy


def test_three_strategies_to_compare():
    assert [s.value for s in ChunkStrategy] == ["fixed_500", "paragraph", "paragraph_item"]
