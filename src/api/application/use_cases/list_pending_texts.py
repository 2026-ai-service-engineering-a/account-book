from __future__ import annotations

from collections.abc import Callable

from api.application.dto import IndexText
from api.application.ports import UnitOfWork

MAX_PENDING = 200


class ListPendingTexts:
    """색인 안 된 텍스트 — agent가 당겨 가서 임베딩한다. api는 agent를 부르지 않는다(4.3).

    거래의 색인 텍스트가 먼저, 남는 자리를 문서 조각의 찾는 글이 채운다(document-rag.md 4장).
    벡터는 같은 text_embeddings에 들어간다 — 색인 워커는 하나다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, model: str, limit: int) -> tuple[IndexText, ...]:
        cap = max(1, min(limit, MAX_PENDING))
        with self._unit_of_work() as uow:
            texts = uow.index.pending(model, cap)
            if len(texts) < cap:
                seen = {t.text_hash for t in texts}
                more = uow.documents.pending(model, cap - len(texts))
                texts += tuple(t for t in more if t.text_hash not in seen)
            return texts
