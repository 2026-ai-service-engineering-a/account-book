from __future__ import annotations

from collections.abc import Mapping

import httpx
from pydantic import ValidationError

from agent.application.dto import StoredProposal
from agent.application.errors import LedgerUnavailable
from agent.application.ports.proposal_book import Closing

from .error_reply import ErrorReply
from .proposal_reply import ProposalReply


class HttpProposalBook:
    """쓰기 제안을 api의 감사 테이블에서 — `GET /v1/runs/{id}`, `/confirm`, `/close`
    (api-contract 6장).

    고치는 둘은 쓰기라 멱등 키가 필요하다. 같은 결정은 같은 키라 다시 보내도 같다.
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

    async def get(self, run_id: str) -> StoredProposal | None:
        response = await self._send("GET", f"/v1/runs/{run_id}", missing_ok=True)
        return self._parse(response) if response is not None else None

    async def confirm(self, run_id: str, call_id: str) -> StoredProposal:
        body: dict[str, object] = {"call_id": call_id}
        key = f"run:{run_id}:confirm"
        response = await self._send("POST", f"/v1/runs/{run_id}/confirm", body, key)
        assert response is not None
        return self._parse(response)

    async def close(
        self,
        run_id: str,
        status: Closing,
        stop_reason: str,
        results: Mapping[str, Mapping[str, object]] | None = None,
    ) -> StoredProposal:
        body: dict[str, object] = {"status": status, "stop_reason": stop_reason}
        if results:
            body["results"] = [{"call_id": k, "result": dict(v)} for k, v in results.items()]
        key = f"run:{run_id}:close:{stop_reason}"
        response = await self._send("POST", f"/v1/runs/{run_id}/close", body, key)
        assert response is not None
        return self._parse(response)

    async def _send(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        key: str | None = None,
        missing_ok: bool = False,
    ) -> httpx.Response | None:
        headers = {"Idempotency-Key": key} if key else None
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(method, path, json=body, headers=headers)
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if missing_ok and response.status_code == 404:
            return None
        if response.is_client_error:
            raise ErrorReply.rejection(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")
        return response

    @staticmethod
    def _parse(response: httpx.Response) -> StoredProposal:
        try:
            return ProposalReply.model_validate_json(response.content).proposal()
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
