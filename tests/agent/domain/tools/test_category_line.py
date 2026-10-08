from __future__ import annotations

from agent.domain.tools import CategoryLine
from agent.domain.values import CategoryId


def test_id_and_name():
    assert CategoryLine(CategoryId("cafe"), "카페").name == "카페"
