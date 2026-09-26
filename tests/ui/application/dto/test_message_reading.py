from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import MessageReading


def test_refusal_leaves_every_field_empty():
    # 못 읽었으면 아무 칸도 채우지 않는다 — 추측으로 채운 칸보다 빈칸이 싸다
    refused = MessageReading(refusal="승인 취소 문자는 아직 읽지 않아요.")
    fields = (refused.direction, refused.amount, refused.occurred_at, refused.account_id)
    assert fields == (None, None, None, None) and refused.merchant is None


def test_is_a_frozen_value():
    reading: MessageReading = MessageReading()
    with pytest.raises(dataclasses.FrozenInstanceError):
        reading.refusal = "x"  # type: ignore[misc]
