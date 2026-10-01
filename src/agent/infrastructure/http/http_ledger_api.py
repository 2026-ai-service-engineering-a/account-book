from __future__ import annotations

import httpx
from pydantic import BaseModel, ValidationError

from agent.application.dto import CategoryQuery, PendingText, SearchResult
from agent.application.errors import LedgerUnavailable

from .pending_reply import PendingReply
from .suggest_reply import SuggestReply


class HttpLedgerApi:
    """api를 HTTP로 부른다. 지금 `API_BASE_URL`은 ui 안의 api 대역을 가리킨다 — api가 서면
    주소만 바뀐다.

    닿지 못했거나, 4xx·5xx거나, 모르는 모양이면 전부 `LedgerUnavailable` 하나로 번역한다.
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

    async def suggest(self, query: CategoryQuery) -> SearchResult:
        body: dict[str, object] = {
            "merchant": query.merchant,
            "memo": query.memo,
            "direction": query.direction.value,
            "embedding_model": query.embedding_model,
            "query_vector": list(query.query_vector) if query.query_vector else None,
        }
        response = await self._send("POST", "/v1/categories/suggest", json=body)
        return self._parse(SuggestReply, response).result()

    async def pending(self, embedding_model: str, limit: int) -> tuple[PendingText, ...]:
        params: dict[str, str | int] = {"model": embedding_model, "limit": limit}
        response = await self._send("GET", "/v1/embeddings/pending", params=params)
        return self._parse(PendingReply, response).texts()

    async def put_embedding(
        self, text_hash: str, embedding_model: str, vector: tuple[float, ...]
    ) -> None:
        # 재시도해도 같은 키가 나온다 — 같은 모델·같은 텍스트면 같은 벡터다(api-contract 3장)
        key = f"emb:{embedding_model}:{text_hash}"
        await self._send(
            "PUT",
            f"/v1/embeddings/{text_hash}",
            json={"model": embedding_model, "vector": list(vector)},
            headers={"Idempotency-Key": key},
        )

    async def _send(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(
                    method, path, json=json, params=params, headers=headers
                )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        return response

    @staticmethod
    def _parse[R: BaseModel](kind: type[R], response: httpx.Response) -> R:
        try:
            return kind.model_validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
