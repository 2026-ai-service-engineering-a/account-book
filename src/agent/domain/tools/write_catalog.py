"""쓰기 도구의 설명과 입력 JSON Schema. v1.0은 `create_transaction` 하나다(ai/chat-capture.md).

쓰기 도구에는 `dry_run` 인자가 없다 — 같은 도구에 경로가 둘 생기면 하나만 테스트된다(tools.md 7장).
"""

from __future__ import annotations

from collections.abc import Mapping

from agent.domain.values import Direction, PaymentMethod

from .tool_name import ToolName
from .tool_spec import ToolSpec

WRITE_TOOLS: Mapping[ToolName, ToolSpec] = {
    ToolName.CREATE_TRANSACTION: ToolSpec(
        ToolName.CREATE_TRANSACTION,
        does="거래 한 건을 기록하자고 제안한다. 사람이 확인 카드에서 누른 뒤에야 기록된다.",
        avoid="이미 있는 거래를 고치거나 지우는 데는 쓰지 않는다 — 그런 쓰기는 채팅에 없다.",
        input_schema={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": [d.value for d in Direction]},
                "amount": {"type": "integer", "minimum": 1},
                "occurred_at": {"type": "string", "format": "date-time"},
                "category_id": {"type": "string"},
                "account": {"type": "string", "enum": [m.value for m in PaymentMethod]},
                "merchant": {"type": "string"},
                "memo": {"type": "string"},
            },
            "required": ["direction", "amount", "occurred_at", "category_id", "account"],
            "additionalProperties": False,
        },
    )
}
