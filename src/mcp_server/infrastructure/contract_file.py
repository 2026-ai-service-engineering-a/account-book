"""agent와 나누는 계약 — src/shared/mcp_tools.json(docs/ai/mcp.md 2장).

agent의 mcp 모드 스냅샷 테스트가 이 파일을 써 낸다. mcp는 뜰 때 읽기만 한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from mcp_server.domain.tools import ToolContract, ToolName

CONTRACT = Path(__file__).parents[2] / "shared" / "mcp_tools.json"


class _Entry(BaseModel):
    name: ToolName  # 모르는 이름이 있으면 뜨지 않는다 — 부를 코드가 없는 도구를 내놓지 않는다
    description: str
    input_schema: dict[str, Any]  # JSON Schema — 바깥과 닿는 자리라 Any다(development-rules 5.2)


def read_contract(path: Path = CONTRACT) -> tuple[ToolContract, ...]:
    entries = TypeAdapter(list[_Entry]).validate_json(path.read_bytes())
    return tuple(ToolContract(e.name, e.description, e.input_schema) for e in entries)
