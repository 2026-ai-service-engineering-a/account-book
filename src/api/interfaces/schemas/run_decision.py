from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class _Result(BaseModel):
    call_id: str = Field(min_length=1, max_length=1000)
    result: dict[str, Any]  # 바깥과 닿는 자리라 Any다(development-rules 5.2)


class RunDecision(BaseModel):
    """쓰기 제안의 결정 — `/confirm`은 `call_id`만, `/close`는 `status`·`stop_reason`·`results`."""

    call_id: str = Field(default="", max_length=1000)
    status: Literal["done", "aborted", "failed"] | None = None
    stop_reason: str = Field(default="", max_length=30)
    results: list[_Result] = Field(default_factory=list, max_length=10)

    def result_map(self) -> dict[str, dict[str, Any]]:
        return {r.call_id: r.result for r in self.results}
