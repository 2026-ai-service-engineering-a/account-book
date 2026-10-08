from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable

from api.application.ports import UnitOfWork
from api.domain.rules.law_chunking import chunk_law
from api.domain.rules.law_markdown import parse_law
from api.domain.values import ChunkStrategy


class LoadDocuments:
    """법령 Markdown들을 문서와 세 전략의 조각으로 넣는다. 몇 번을 돌려도 같다.

    문서마다 조각을 통째로 갈아 끼운다 — 청킹 규칙을 고친 뒤 다시 돌리면 옛 조각이 남지 않는다.
    한 트랜잭션이다. 하나라도 못 읽으면 아무것도 넣지 않는다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, texts: Iterable[str]) -> Counter[ChunkStrategy]:
        """전략별로 넣은 조각 수."""
        counts: Counter[ChunkStrategy] = Counter()
        with self._unit_of_work() as uow:
            for text in texts:
                document = parse_law(text)
                chunks = [c for s in ChunkStrategy for c in chunk_law(document, s)]
                uow.documents.replace(document, chunks)
                counts.update(c.strategy for c in chunks)
            uow.commit()
        return counts
