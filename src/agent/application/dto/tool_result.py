from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .tool_error import ToolError
from .tool_meta import ToolMeta


@dataclass(frozen=True, slots=True)
class ToolResult:
    """결과 봉투(ai/tools.md 3.1). 성공도 실패도 같은 모양이다 — 실패도 관찰이다."""

    call_id: str
    data: Mapping[str, object] | None = None
    meta: ToolMeta | None = None
    error: ToolError | None = None

    def __post_init__(self) -> None:
        if (self.data is None) == (self.error is None):
            raise ValueError("봉투에는 data와 error 중 하나만 있다")

    @property
    def ok(self) -> bool:
        return self.error is None

    def envelope(self) -> dict[str, object]:
        """모델과 감사 로그에 그대로 넣을 JSON 모양."""
        out: dict[str, object] = {"call_id": self.call_id, "ok": self.ok}
        if self.error is not None:
            out["error"] = {
                "code": self.error.code,
                "retryable": self.error.retryable,
                "hint": self.error.hint,
            }
            return out
        out["data"] = self.data
        if self.meta is not None:
            meta: dict[str, object] = {
                "row_count": self.meta.row_count,
                "truncated": self.meta.truncated,
                "elapsed_ms": self.meta.elapsed_ms,
            }
            if self.meta.periods:
                meta["periods"] = {
                    k: {"from": r.start.isoformat(), "to": r.end.isoformat()}
                    for k, r in self.meta.periods.items()
                }
            if self.meta.note:
                meta["note"] = self.meta.note
            out["meta"] = meta
        return out
