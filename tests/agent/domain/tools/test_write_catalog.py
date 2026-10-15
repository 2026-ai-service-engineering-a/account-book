from __future__ import annotations

from agent.domain.tools import WRITE_TOOLS, Permission, ToolName


def test_one_write_tool_with_no_dry_run():
    assert list(WRITE_TOOLS) == [ToolName.CREATE_TRANSACTION]
    spec = WRITE_TOOLS[ToolName.CREATE_TRANSACTION]
    assert spec.name.permission is Permission.WRITE_CONFIRM
    # 제안은 인자가 아니라 흐름의 단계다(ai/tools.md 7장)
    assert "dry_run" not in spec.input_schema["properties"]  # type: ignore[operator]
    assert spec.input_schema["additionalProperties"] is False
