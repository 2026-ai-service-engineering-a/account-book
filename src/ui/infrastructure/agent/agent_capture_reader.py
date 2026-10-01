from __future__ import annotations

import logging
from datetime import datetime

import httpx
from pydantic import ValidationError

from ui.application.dto import Direction, MessageReading
from ui.application.values import AccountId, Money

from .agent_capture_reply import AgentCaptureReply

_UNAVAILABLE = "지금은 AI가 읽을 수 없어요. 칸을 직접 채워 주세요."
_log = logging.getLogger(__name__)


class AgentCaptureReader:
    """AI 자리 ④의 진짜. agent의 `POST /capture`를 부른다.

    ui는 문자를 해석하지 않는다. 보내고, 구조만 받는다. agent가 없거나 죽었거나 이상한
    답을 주면 못 읽었다고 한다 — 칸은 그대로고 폼은 손으로 돈다(docs/ai 원칙 8).
    """

    def __init__(
        self,
        base_url: str,
        timezone: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timezone = timezone
        self._timeout = timeout
        self._transport = transport

    async def read(self, text: str, now: datetime) -> MessageReading:
        body = {"text": text, "now": now.isoformat(), "timezone": self._timezone}
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post("/capture", json=body)
            response.raise_for_status()
            reply = AgentCaptureReply.model_validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 보낸 원문은 남기지 않는다(development-rules 6.4).
            _log.warning("agent capture failed: %s", type(error).__name__)
            return MessageReading(refusal=_UNAVAILABLE)
        return _reading(reply)


def _reading(reply: AgentCaptureReply) -> MessageReading:
    if reply.refusal or reply.amount is None:
        return MessageReading(refusal=reply.refusal or _UNAVAILABLE)
    return MessageReading(
        direction=Direction(reply.direction) if reply.direction else None,
        amount=Money(reply.amount),
        occurred_at=reply.occurred_at,
        # 결제수단의 종류가 곧 대역 카탈로그의 id다. 진짜 api가 오면 계좌 목록에서 찾는다.
        account_id=AccountId(reply.payment_method) if reply.payment_method else None,
        merchant=reply.merchant or None,
    )
