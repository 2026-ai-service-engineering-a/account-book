from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import ChunkId, ChunkStrategy, DocumentId


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """검색의 단위. `body`는 원문 그대로 — 화면의 인용이다. 찾는 글은 `search_text`다.

    `search_text`에서만 개정 꼬리표를 뺀다(document-rag.md 3.1). 전략에 따라 조 제목·항 머리가
    붙는다. `text_hash`는 그 글의 해시라서, 같은 글을 가진 조각은 임베딩 하나를 나눠 쓴다.
    """

    id: ChunkId
    document_id: DocumentId
    strategy: ChunkStrategy
    heading: str  # 화면에 보이는 제목 — "제126조의2(…) ②"
    body: str
    search_text: str
    text_hash: str
    position: int  # 같은 문서·같은 전략 안에서의 순서
