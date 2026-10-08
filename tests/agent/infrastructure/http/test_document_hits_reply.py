from __future__ import annotations

from datetime import date

from agent.domain.values import ChunkStrategy
from agent.infrastructure.http.document_hits_reply import DocumentHitsReply

HIT = {
    "id": "paragraph:할부거래에 관한 법률/제8조/1",
    "document_id": "할부거래에 관한 법률",
    "title": "할부거래에 관한 법률",
    "effective_date": "2026-09-08",
    "strategy": "paragraph",
    "heading": "제8조(청약의 철회) ①",
    "body": "① 소비자는 … 청약을 철회할 수 있다.",
    "score": 0.81,
}


def test_reads_the_hits_in_order():
    (chunk,) = DocumentHitsReply.model_validate([HIT]).chunks()
    assert (chunk.strategy, chunk.effective_date, chunk.score) == (
        ChunkStrategy.PARAGRAPH,
        date(2026, 9, 8),
        0.81,
    )
