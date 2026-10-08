from __future__ import annotations

from datetime import date
from typing import Literal, TypedDict

from pydantic import TypeAdapter, ValidationError

from ui.application.dto import ChunkStrategy, DocumentHit, DocumentResults, SearchMode
from ui.application.errors import LedgerUnavailable

from .api_client import ApiClient


# 응답 모양. 이 게이트웨이만 쓰는 TypedDict라 같은 파일에 둔다(development-rules 1.2의 예외).
class _HitItem(TypedDict):
    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float


_HITS = TypeAdapter(list[_HitItem])


class HttpDocumentGateway:
    """문서 조각 찾기 — api의 `GET /v1/documents/search`."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def search(
        self,
        query: str,
        strategy: ChunkStrategy,
        k: int = 5,
        mode: SearchMode = SearchMode.KEYWORD,
    ) -> DocumentResults:
        """낱말로만 찾는다 — 뜻으로 찾으려면 질문을 임베딩할 agent가 있어야 한다."""
        hits = await self._keyword(query, strategy, k)
        return DocumentResults(hits, SearchMode.KEYWORD, fell_back=mode is not SearchMode.KEYWORD)

    async def _keyword(
        self, query: str, strategy: ChunkStrategy, k: int
    ) -> tuple[DocumentHit, ...]:
        params: dict[str, str | int] = {"q": query, "k": k, "strategy": strategy.value}
        response = await self._client.request("GET", "/v1/documents/search", params=params)
        try:
            items = _HITS.validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
        return tuple(
            DocumentHit(
                id=i["id"],
                title=i["title"],
                effective_date=i["effective_date"],
                strategy=ChunkStrategy(i["strategy"]),
                heading=i["heading"],
                body=i["body"],
                score=i["score"],
            )
            for i in items
        )
