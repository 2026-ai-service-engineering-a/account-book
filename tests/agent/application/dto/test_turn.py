from __future__ import annotations

import pytest

from agent.application.dto import ToolCall, Turn


def test_roles_carry_what_they_carry():
    Turn("user", "저번 주 카페 몇 번?")
    Turn("assistant", tool_calls=(ToolCall("c1", "count_frequency", {}),))
    Turn("tool", '{"ok": true}', call_id="c1")


@pytest.mark.parametrize(
    "build",
    [
        lambda: Turn("tool", "{}"),  # 어느 호출의 결과인지 없다
        lambda: Turn("user", "x", call_id="c1"),
        lambda: Turn("user", tool_calls=(ToolCall("c1", "x", {}),)),
    ],
)
def test_mixed_up_turns_are_refused(build):
    with pytest.raises(ValueError):
        build()
