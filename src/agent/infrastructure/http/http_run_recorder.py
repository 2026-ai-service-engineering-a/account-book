from __future__ import annotations

import httpx

from agent.application.dto import RunRecord
from agent.application.errors import LedgerUnavailable

from .error_reply import ErrorReply


class HttpRunRecorder:
    """감사 로그를 api의 `POST /v1/runs`로 보낸다(api-contract 6장).

    키는 `run:{run_id}`다 — 다시 보내도 한 줄이다. 타임아웃은 LLM 호출보다 짧게 둔다. 기록을
    기다리느라 답이 늦어지면 안 된다.
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

    async def record(self, run: RunRecord, model: str) -> None:
        body: dict[str, object] = {
            "id": run.run_id,
            "seat": run.seat.value,
            "flow": run.seat.flow,
            "utterance": run.utterance,
            "model": model,
            "steps": run.steps,
            "tokens": run.tokens,
            "cost_usd": round(run.cost_usd, 6),
            "status": _status(run),
            "stop_reason": run.stop_reason,
            "tool_calls": [
                {
                    "call_id": c.call_id,
                    "tool": c.tool,
                    "args": dict(c.args),
                    "result": dict(c.result) if c.result is not None else None,
                }
                for c in run.tool_calls
            ],
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(
                    "/v1/runs", json=body, headers={"Idempotency-Key": f"run:{run.run_id}"}
                )
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_client_error:
            raise ErrorReply.rejection(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")


def _status(run: RunRecord) -> str:
    if run.failed:
        return "failed"
    return "awaiting_confirmation" if run.awaiting else "done"
