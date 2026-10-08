from __future__ import annotations

from ui.application.dto import ChunkStrategy


def test_three_strategies_with_labels_for_the_select():
    assert [s.value for s in ChunkStrategy] == ["paragraph", "paragraph_item", "fixed_500"]
    assert ChunkStrategy.FIXED_500.label == "500자씩(기준선)"
