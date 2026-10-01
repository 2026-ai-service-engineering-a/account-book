from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, PositiveInt

from .agent_category_reply import AgentCategoryReply


class AgentCaptureReply(BaseModel):
    """agent `POST /capture`의 응답 본문. 모양이 다르면 받지 않는다 — 바깥에서 온 JSON이다."""

    direction: Literal["expense", "income"] | None
    amount: PositiveInt | None
    occurred_at: AwareDatetime | None
    payment_method: Literal["card", "cash", "bank"] | None
    merchant: str | None
    refusal: str
    category: AgentCategoryReply | None = None
