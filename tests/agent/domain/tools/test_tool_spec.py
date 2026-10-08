from __future__ import annotations

import pytest

from agent.domain.tools import ToolName, ToolSpec


def test_description_is_what_then_when_not():
    spec = ToolSpec(ToolName.COUNT_FREQUENCY, "센다.", "합계면 쓰지 않는다.", {"type": "object"})
    assert spec.description == "센다.\n합계면 쓰지 않는다."


@pytest.mark.parametrize(
    ("does", "avoid"), [("센다.", ""), ("", "쓰지 않는다."), ("센다.\n또", "x")]
)
def test_two_single_lines_both_present(does, avoid):
    with pytest.raises(ValueError):
        ToolSpec(ToolName.COUNT_FREQUENCY, does, avoid, {})
