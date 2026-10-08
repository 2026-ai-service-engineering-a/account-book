from __future__ import annotations

import dataclasses

from api.application.dto import ChunkHit


def test_is_a_frozen_dataclass():
    assert ChunkHit.__dataclass_params__.frozen  # type: ignore[attr-defined]  # 공개 API가 아니다
    assert [f.name for f in dataclasses.fields(ChunkHit)] == [
        "chunk",
        "score",
        "title",
        "effective_date",
    ]
