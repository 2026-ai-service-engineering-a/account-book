from __future__ import annotations

import httpx

from mcp_server.application.dto import RunEntry
from mcp_server.application.errors import LedgerUnavailable

from .error_reply import ErrorReply

# 바깥 클라이언트가 어느 모델을 쓰는지 우리는 모른다(docs/ai/mcp.md 7.2)
EXTERNAL_MODEL = "external"


class HttpRunLog:
    """감사 로그를 api의 `POST /v1/runs`로 보낸다(api-contract 6장).

    `seat=mcp`, `flow=direct` — LLM 없이 도구 하나다. 토큰·비용은 클라이언트의 것이라 0이다.
    키는 `run:{run_id}`다 — 다시 보내도 한 줄이다.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 api를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._transport = transport

    async def record(self, entry: RunEntry) -> None:
        body: dict[str, object] = {
            "id": entry.run_id,
            "seat": "mcp",
            "flow": "direct",
            "utterance": "",
            "model": EXTERNAL_MODEL,
            "steps": 0,
            "tokens": 0,
            "cost_usd": 0,
            "status": "failed" if entry.failed else "done",
            "stop_reason": entry.stop_reason,
            "tool_calls": [
                {
                    "call_id": entry.run_id,
                    "tool": entry.tool,
                    "args": dict(entry.args),
                    "result": dict(entry.envelope),
                }
            ],
            "client": entry.client,
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(
                    "/v1/runs", json=body, headers={"Idempotency-Key": f"run:{entry.run_id}"}
                )
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_client_error:
            raise ErrorReply.rejection(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")
