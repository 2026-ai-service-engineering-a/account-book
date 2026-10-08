from __future__ import annotations

import dataclasses

from agent.domain.tools import TransactionLine


def test_is_a_frozen_dataclass():
    assert TransactionLine.__dataclass_params__.frozen  # type: ignore[attr-defined]  # 공개 API가 아니다
    assert [f.name for f in dataclasses.fields(TransactionLine)][:2] == ["id", "occurred_at"]
