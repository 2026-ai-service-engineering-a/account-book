from __future__ import annotations

from api.domain.values import ChunkId


def test_carries_strategy_and_path():
    strategy, _, path = ChunkId("paragraph:소득세법/제59조의4/2").partition(":")
    assert (strategy, path.split("/")) == ("paragraph", ["소득세법", "제59조의4", "2"])
