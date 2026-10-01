from __future__ import annotations

import dataclasses

import pytest

from agent.application.dto import Prompt


def test_is_a_frozen_value():
    prompt = Prompt(name="capture", system="s", user="u", schema={"type": "object"})
    with pytest.raises(dataclasses.FrozenInstanceError):
        prompt.user = "x"  # type: ignore[misc]
