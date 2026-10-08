from __future__ import annotations

from ui.application.dto import ChunkStrategy, DocumentHit

from .document_samples import SAMPLES


class MemoryDocumentGateway:
    """문서 검색의 대역 — 조문 네 줄을 글자 세 개짜리 조각의 겹침으로 찾는다(pg_trgm 흉내).

    전략을 가리지 않는다. 조각이 넷뿐이라 나눌 것이 없다. 진짜 검색은 api가 한다.
    """

    async def search(
        self, query: str, strategy: ChunkStrategy, k: int = 5
    ) -> tuple[DocumentHit, ...]:
        wanted = _trigrams(" ".join(query.split()))
        if not query.strip():
            return ()
        hits = [
            DocumentHit(
                id=f"{strategy.value}:{path}",
                title=title,
                effective_date=effective,
                strategy=strategy,
                heading=heading,
                body=body,
                score=round(len(wanted & _trigrams(body)) / len(wanted), 4),
            )
            for path, title, effective, heading, body in SAMPLES
        ]
        hits.sort(key=lambda h: -h.score)
        return tuple(hits[:k])


def _trigrams(text: str) -> set[str]:
    padded = f"  {text} "
    return {padded[i : i + 3] for i in range(len(padded) - 2)}
