from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunEntry:
    """감사 로그의 한 줄 — mcp 호출 하나가 실행 하나다(docs/ai/mcp.md 7.3).

    LLM은 바깥 클라이언트의 것이라 우리 쪽 흐름은 `direct`, 발화는 없다. 인자와 결과는
    여기에만 남고 운영 로그에는 없다(development-rules 6.4).
    """

    run_id: str
    tool: str
    args: Mapping[str, object]
    envelope: Mapping[str, object]
    client: str  # MCP 초기화에서 받은 클라이언트 이름

    @property
    def failed(self) -> bool:
        """api에 닿지 못해 답을 못 낸 것만 실패다. 인자를 고치라는 답도 답이다."""
        return self._code == "internal_error"

    @property
    def stop_reason(self) -> str:
        return self._code or "answered"

    @property
    def _code(self) -> str:
        error = self.envelope.get("error")
        code = error.get("code") if isinstance(error, Mapping) else None
        return code if isinstance(code, str) else ""
