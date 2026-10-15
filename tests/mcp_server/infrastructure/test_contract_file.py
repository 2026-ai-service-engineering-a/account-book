from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from mcp_server.domain.tools import ToolName
from mcp_server.infrastructure.contract_file import CONTRACT, read_contract


def test_reads_the_shared_contract_the_agent_writes():
    assert CONTRACT.parts[-2:] == ("shared", "mcp_tools.json")
    contract = read_contract()
    assert [c.name for c in contract] == list(ToolName)
    assert all(c.description and c.input_schema["type"] == "object" for c in contract)


def test_a_tool_mcp_cannot_call_is_refused(tmp_path: Path):
    path = tmp_path / "mcp_tools.json"
    path.write_text(
        '[{"name": "delete_transaction", "description": "지운다", "input_schema": {}}]',
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        read_contract(path)
