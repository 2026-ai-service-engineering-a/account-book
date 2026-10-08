from __future__ import annotations

import dataclasses
import logging

from agent.application.dto import DocumentQuery, Retrieval
from agent.application.errors import ModelUnavailable
from agent.application.ports import Embedder, LedgerApi
from agent.domain.values import ChunkStrategy, SearchMode

from .sync_index import SyncIndex

_log = logging.getLogger(__name__)


class Retrieve:
    """문서 조각 찾기(docs/ai/document-rag.md 4장의 질의 쪽, 생성 전까지). 생성 모델은 없다.

    벡터·하이브리드면 색인 안 된 조각을 먼저 임베딩하고(SyncIndex), 질문을 임베딩해 api에 묻는다.
    임베딩 제공자에 닿지 못하면 키워드로 물러서고 그 사실을 남긴다 — 찾기는 멈추지 않는다(원칙 8).
    """

    def __init__(
        self, ledger: LedgerApi, embedder: Embedder | None, index: SyncIndex | None
    ) -> None:
        self._ledger = ledger
        self._embedder = embedder
        self._index = index

    async def __call__(
        self, question: str, strategy: ChunkStrategy, k: int, mode: SearchMode
    ) -> Retrieval:
        """api에 닿지 못하면 `LedgerUnavailable`."""
        query = DocumentQuery(" ".join(question.split()), strategy, k)
        if mode is SearchMode.KEYWORD:
            return Retrieval(mode, False, await self._ledger.search_documents(query))
        if self._embedder is None:  # EMBEDDING_MODEL이 비었다 — 벡터 단계를 끈 구성
            return await self._keyword(query)
        if self._index is not None:
            try:
                await self._index.run()
            except ModelUnavailable:
                # 색인이 늦는 것은 품질 문제다. 있는 벡터로 계속한다(category-suggestion-rag 4.3)
                _log.warning("embedding sync skipped")
        try:
            (vector,) = await self._embedder.embed([query.text])
        except ModelUnavailable:
            _log.warning("query embedding failed — keyword fallback")
            return await self._keyword(query)
        query = dataclasses.replace(
            query, mode=mode, embedding_model=self._embedder.model, query_vector=vector
        )
        return Retrieval(mode, False, await self._ledger.search_documents(query))

    async def _keyword(self, query: DocumentQuery) -> Retrieval:
        return Retrieval(SearchMode.KEYWORD, True, await self._ledger.search_documents(query))
