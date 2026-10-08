from __future__ import annotations

import dataclasses
import logging
from datetime import date
from typing import Literal, TypedDict

import httpx
from pydantic import TypeAdapter, ValidationError

from ui.application.dto import AnswerStatus, ChunkStrategy, DocumentAnswer, DocumentHit
from ui.application.ports import DocumentAnswerer

_log = logging.getLogger(__name__)


# agent `POST /ask`의 응답 모양. 이 클래스만 쓴다(development-rules 1.2의 예외).
class _Chunk(TypedDict):
    id: str
    title: str
    effective_date: date
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"]
    heading: str
    body: str
    score: float


class _Reply(TypedDict):
    status: Literal["answered", "abstained", "search_only"]
    answer: str
    citations: list[_Chunk]
    chunks: list[_Chunk]
    reason: str


_REPLY = TypeAdapter(_Reply)


class AgentDocumentAnswerer:
    """문서 Q&A의 진짜 — agent의 `POST /ask`. 조문을 인용한 답을 받는다.

    ui는 판단하지 않는다. agent가 없거나 죽으면 대역(낱말로 찾은 조문만)으로 물러서고 까닭을
    밝힌다 — 화면은 멈추지 않는다(docs/ai 원칙 8).
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        fallback: DocumentAnswerer,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._fallback = fallback
        self._transport = transport

    async def ask(self, question: str) -> DocumentAnswer:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post("/ask", json={"q": question})
            response.raise_for_status()
            reply = _REPLY.validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 질문은 남기지 않는다(development-rules 6.4)
            _log.warning("agent ask failed: %s", type(error).__name__)
            found = await self._fallback.ask(question)
            return dataclasses.replace(found, reason="지금은 AI에 닿지 못해 찾은 조문만 보여요.")
        return DocumentAnswer(
            status=AnswerStatus(reply["status"]),
            answer=reply["answer"],
            citations=tuple(_hit(c) for c in reply["citations"]),
            chunks=tuple(_hit(c) for c in reply["chunks"]),
            reason=reply["reason"],
        )


def _hit(chunk: _Chunk) -> DocumentHit:
    return DocumentHit(
        id=chunk["id"],
        title=chunk["title"],
        effective_date=chunk["effective_date"],
        strategy=ChunkStrategy(chunk["strategy"]),
        heading=chunk["heading"],
        body=chunk["body"],
        score=chunk["score"],
    )
