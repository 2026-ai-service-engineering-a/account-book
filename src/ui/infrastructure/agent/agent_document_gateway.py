from __future__ import annotations

import dataclasses
import logging
from datetime import date
from typing import Literal, TypedDict

import httpx
from pydantic import TypeAdapter, ValidationError

from ui.application.dto import ChunkStrategy, DocumentHit, DocumentResults, SearchMode
from ui.application.ports import DocumentGateway

_log = logging.getLogger(__name__)


# agent `POST /retrieve`의 응답 모양. 이 게이트웨이만 쓴다(development-rules 1.2의 예외).
class _Chunk(TypedDict):
    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float


class _Reply(TypedDict):
    mode: Literal["keyword", "vector", "hybrid"]
    fell_back: bool
    chunks: list[_Chunk]


_REPLY = TypeAdapter(_Reply)


class AgentDocumentGateway:
    """문서 찾기의 AI 쪽 — agent의 `POST /retrieve`. 질문을 임베딩해 뜻으로도 찾는다.

    ui는 임베딩을 모른다. agent가 없거나 죽으면 api의 낱말 검색으로 물러서고 그 사실을 밝힌다 —
    화면은 멈추지 않는다(docs/ai 원칙 8).
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        fallback: DocumentGateway,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._fallback = fallback
        self._transport = transport

    async def search(
        self,
        query: str,
        strategy: ChunkStrategy,
        k: int | None = None,
        mode: SearchMode = SearchMode.KEYWORD,
    ) -> DocumentResults:
        # k를 비우면 agent의 DOC_TOP_K를 쓴다 — 기본값은 agent 한 곳에 있다
        body: dict[str, object] = {"q": query, "strategy": strategy.value, "mode": mode.value}
        if k is not None:
            body["k"] = k
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post("/retrieve", json=body)
            response.raise_for_status()
            reply = _REPLY.validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 질문은 남기지 않는다(development-rules 6.4)
            _log.warning("agent retrieve failed: %s", type(error).__name__)
            found = await self._fallback.search(query, strategy, k)
            return dataclasses.replace(found, fell_back=mode is not SearchMode.KEYWORD)
        hits = tuple(
            DocumentHit(
                id=c["id"],
                title=c["title"],
                effective_date=c["effective_date"],
                strategy=ChunkStrategy(c["strategy"]),
                heading=c["heading"],
                body=c["body"],
                score=c["score"],
            )
            for c in reply["chunks"]
        )
        return DocumentResults(hits, SearchMode(reply["mode"]), reply["fell_back"])
