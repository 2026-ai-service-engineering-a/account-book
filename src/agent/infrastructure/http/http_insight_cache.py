from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

import httpx
from pydantic import ValidationError

from agent.application.errors import LedgerUnavailable

from .error_reply import ErrorReply
from .insight_cache_reply import InsightCacheReply


class HttpInsightCache:
    """리포트 캐시를 api의 `/v1/insights/cache/{key}`로(api-contract 6장)."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 api를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._transport = transport

    async def get(self, key: str) -> Mapping[str, object] | None:
        response = await self._send("GET", key)
        try:
            return InsightCacheReply.model_validate_json(response.content).body
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error

    async def put(self, key: str, body: Mapping[str, object]) -> None:
        # 같은 키에 다른 답(모델이 다르게 쓴 것)을 쓰면 새 요청이다 — 본문 해시를 멱등 키에 붙인다
        payload: dict[str, object] = {"body": dict(body)}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
        await self._send("PUT", key, payload, {"Idempotency-Key": f"insight:{key[:16]}:{digest}"})

    async def _send(
        self,
        method: str,
        key: str,
        json_body: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(
                    method, f"/v1/insights/cache/{key}", json=json_body, headers=headers
                )
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_client_error:
            raise ErrorReply.rejection(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")
        return response
