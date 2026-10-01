from __future__ import annotations

from api.infrastructure.db.rows import ToolCallRow


def test_maps_the_tool_calls_table():
    assert ToolCallRow.__tablename__ == "tool_calls"
