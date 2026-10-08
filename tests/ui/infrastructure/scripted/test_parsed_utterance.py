from __future__ import annotations

import dataclasses

import pytest

from ui.application.dto import Direction
from ui.application.values import AccountId
from ui.infrastructure.scripted.parsed_utterance import ParsedUtterance


def test_is_a_frozen_value():
    parsed = ParsedUtterance(
        None, 0, False, None, AccountId("card"), Direction.EXPENSE, "", True, False, False
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        parsed.merchant = "x"  # type: ignore[misc]
