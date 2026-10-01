from __future__ import annotations

import logging

import httpx
from pydantic import ValidationError

from ui.application.dto import CategorySuggestion, Direction

from .agent_category_reply import AgentCategoryReply

_UNAVAILABLE = "지금은 추천할 수 없어요. 직접 골라 주세요."
_log = logging.getLogger(__name__)


class AgentCategorySuggester:
    """AI 자리 ②의 진짜. agent의 `POST /classify`를 부른다 — 카테고리 옆 AI 버튼.

    ui는 판단하지 않는다. agent가 없거나 죽었거나 이상한 답을 주면 고르지 못했다고 한다.
    셀렉트는 그대로고 사람이 고른다(docs/ai 원칙 8).
    """

    def __init__(
        self, base_url: str, timeout: float, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._transport = transport

    async def suggest(self, merchant: str, memo: str, direction: Direction) -> CategorySuggestion:
        body = {"merchant": merchant, "memo": memo, "direction": direction.value}
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post("/classify", json=body)
            response.raise_for_status()
            reply = AgentCategoryReply.model_validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 가맹점명은 남기지 않는다(development-rules 6.4)
            _log.warning("agent classify failed: %s", type(error).__name__)
            return CategorySuggestion(None, _UNAVAILABLE)
        return reply.suggestion()
