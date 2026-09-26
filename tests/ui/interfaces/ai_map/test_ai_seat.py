from __future__ import annotations

import dataclasses

import pytest

from ui.interfaces.ai_map import SEATS, AiSeat


def test_is_a_frozen_value():
    seat: AiSeat = SEATS[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        seat.flow = "ReAct"  # type: ignore[misc]
