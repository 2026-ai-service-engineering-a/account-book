from __future__ import annotations

from datetime import date

import httpx
from pydantic import BaseModel, ValidationError

from agent.application.dto import (
    CategoryQuery,
    DocumentQuery,
    PendingText,
    RetrievedChunk,
    SearchResult,
    TransactionFilter,
)
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.domain.tools import (
    BudgetLine,
    CategoryLine,
    CategoryShift,
    Frequency,
    SpendingTotals,
    TransactionList,
)
from agent.domain.values import CategoryId, Direction, TimeRange

from .budget_status_reply import BudgetStatusReply
from .categories_reply import CategoriesReply
from .compare_reply import CompareReply
from .document_hits_reply import DocumentHitsReply
from .error_reply import ErrorReply
from .frequency_reply import FrequencyReply
from .pending_reply import PendingReply
from .suggest_reply import SuggestReply
from .totals_reply import TotalsReply
from .transaction_page_reply import TransactionPageReply

type _Params = dict[str, str | int]


class HttpLedgerApi:
    """api를 HTTP로 부른다.

    4xx와 에러 코드는 `LedgerRejected`로 — 모델이 인자를 고칠 수 있는 실패다. 닿지 못했거나
    5xx거나 모르는 모양이면 `LedgerUnavailable`. 재시도하지 않는다 — 루프의 일이다
    (ai/agent-loop.md 7장).
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

    async def transactions(self, where: TransactionFilter, limit: int) -> TransactionList:
        params = _filter(where) | {"limit": limit}
        response = await self._send("GET", "/v1/transactions", params=params)
        return self._parse(TransactionPageReply, response).page()

    async def summary(self, where: TransactionFilter) -> SpendingTotals:
        response = await self._send("GET", "/v1/summary", params=_filter(where))
        return self._parse(TotalsReply, response).totals()

    async def frequency(self, where: TransactionFilter) -> Frequency:
        response = await self._send("GET", "/v1/stats/frequency", params=_filter(where))
        return self._parse(FrequencyReply, response).frequency()

    async def compare(
        self, a: TimeRange, b: TimeRange, category_id: CategoryId | None
    ) -> tuple[CategoryShift, ...]:
        params: _Params = {
            "a_from": a.start.isoformat(),
            "a_to": a.end.isoformat(),
            "b_from": b.start.isoformat(),
            "b_to": b.end.isoformat(),
        }
        if category_id:
            params["category_id"] = category_id
        response = await self._send("GET", "/v1/stats/compare", params=params)
        return self._parse(CompareReply, response).shifts()

    async def budget_status(
        self, month: date, category_id: CategoryId | None
    ) -> tuple[BudgetLine, ...]:
        params: _Params = {"period": f"{month.year:04d}-{month.month:02d}"}
        if category_id:
            params["category_id"] = category_id
        response = await self._send("GET", "/v1/budgets/status", params=params)
        return self._parse(BudgetStatusReply, response).lines()

    async def categories(self) -> tuple[CategoryLine, ...]:
        response = await self._send("GET", "/v1/categories")
        return self._parse(CategoriesReply, response).lines()

    async def search_documents(self, query: DocumentQuery) -> tuple[RetrievedChunk, ...]:
        body: dict[str, object] = {
            "q": query.text,
            "k": query.k,
            "strategy": query.strategy.value,
            "mode": query.mode.value,
            "embedding_model": query.embedding_model,
            "query_vector": list(query.query_vector) if query.query_vector else None,
        }
        response = await self._send("POST", "/v1/documents/search", json=body)
        return self._parse(DocumentHitsReply, response).chunks()

    async def _send(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: _Params | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(
                    method, path, json=json, params=params, headers=headers
                )
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_client_error:
            raise _rejected(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")
        return response

    @staticmethod
    def _parse[R: BaseModel](kind: type[R], response: httpx.Response) -> R:
        try:
            return kind.model_validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error


def _filter(where: TransactionFilter) -> _Params:
    """시각은 오프셋을 붙여 보낸다. `+`는 httpx가 %2B로 인코딩한다(api-contract 6장)."""
    params: _Params = {"from": where.period.start.isoformat(), "to": where.period.end.isoformat()}
    if where.category_id:
        params["category_id"] = where.category_id
    if where.text:
        params["q"] = where.text
    if where.direction is not None:
        params["direction"] = Direction(where.direction).value
    return params


def _rejected(response: httpx.Response) -> LedgerUnavailable:
    """4xx 본문의 `code`를 읽는다. 모르는 모양의 4xx는 거절이 아니라 고장이다."""
    try:
        error = ErrorReply.model_validate_json(response.content).error
    except ValidationError:
        return LedgerUnavailable(f"HTTP {response.status_code}")
    return LedgerRejected(response.status_code, error["code"], error.get("details", {}))
