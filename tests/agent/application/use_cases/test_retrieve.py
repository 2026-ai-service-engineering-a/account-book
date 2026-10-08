from __future__ import annotations

import asyncio
from datetime import date

from agent.application.dto import DocumentQuery, PendingText, Retrieval, RetrievedChunk
from agent.application.use_cases import Retrieve, SyncIndex
from agent.domain.values import ChunkStrategy, SearchMode
from tests.agent.conftest import FakeEmbedder, FakeLedger

CHUNK = RetrievedChunk(
    "paragraph:할부거래에 관한 법률/제8조/1",
    "할부거래에 관한 법률",
    date(2026, 9, 8),
    ChunkStrategy.PARAGRAPH,
    "제8조(청약의 철회) ①",
    "① 소비자는 … 철회할 수 있다.",
    0.8,
)


def ledger(pending: tuple[PendingText, ...] = ()) -> FakeLedger:
    return FakeLedger(pending=pending, replies={"search_documents": (CHUNK,)})


def run(retrieve: Retrieve, mode: SearchMode, question: str = " 노트북  취소 ") -> Retrieval:
    return asyncio.run(retrieve(question, ChunkStrategy.PARAGRAPH, 3, mode))


def asked(found: FakeLedger) -> DocumentQuery:
    ((_, (query,)),) = [c for c in found.calls if c[0] == "search_documents"]
    assert isinstance(query, DocumentQuery)
    return query


def test_keyword_never_embeds():
    found, embedder = ledger(), FakeEmbedder()
    result = run(Retrieve(found, embedder, SyncIndex(found, embedder)), SearchMode.KEYWORD)
    assert result == Retrieval(SearchMode.KEYWORD, False, (CHUNK,))
    assert embedder.calls == [] and asked(found).query_vector is None
    assert asked(found).text == "노트북 취소"


def test_vector_indexes_pending_chunks_first_then_embeds_the_question():
    found, embedder = ledger((PendingText("h1", "조문 글"),)), FakeEmbedder()
    result = run(Retrieve(found, embedder, SyncIndex(found, embedder)), SearchMode.HYBRID)
    assert result.mode is SearchMode.HYBRID and not result.fell_back
    assert embedder.calls == [["조문 글"], ["노트북 취소"]]  # 색인이 먼저, 질문이 다음
    assert found.puts == {"h1": (4.0, 1.0)}
    query = asked(found)
    assert (query.mode, query.embedding_model, query.query_vector) == (
        SearchMode.HYBRID,
        "fake/embedding@2",
        (6.0, 1.0),
    )


def test_without_an_embedder_it_falls_back_to_keyword_and_says_so():
    found = ledger()
    result = run(Retrieve(found, None, None), SearchMode.VECTOR)
    assert (result.mode, result.fell_back) == (SearchMode.KEYWORD, True)
    assert asked(found).mode is SearchMode.KEYWORD


def test_an_embedding_outage_falls_back_instead_of_failing():
    found, embedder = ledger((PendingText("h1", "조문 글"),)), FakeEmbedder(fail=True)
    result = run(Retrieve(found, embedder, SyncIndex(found, embedder)), SearchMode.VECTOR)
    assert (result.mode, result.fell_back, result.chunks) == (SearchMode.KEYWORD, True, (CHUNK,))
