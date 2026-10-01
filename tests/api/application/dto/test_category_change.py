from __future__ import annotations

import dataclasses

from api.application.dto import CategoryChange


def test_is_a_frozen_dataclass():
    assert dataclasses.is_dataclass(CategoryChange)
    assert CategoryChange.__dataclass_params__.frozen  # type: ignore[attr-defined]  # 공개 API가 아니다
