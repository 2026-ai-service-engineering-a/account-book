from __future__ import annotations

from api.application.ports import UnitOfWork
from api.domain.errors import InvalidEmbedding
from api.domain.values import EMBEDDING_DIMENSIONS


class PutEmbedding:
    """색인 텍스트 하나의 벡터를 저장한다. 커밋은 부르는 쪽(멱등 쓰기)이 한다.

    차원이 다르면 받지 않는다 — 다른 모델이나 차원으로 임베딩한 것이고, 섞이면 거리가 뜻을 잃는다.
    """

    def __call__(
        self, uow: UnitOfWork, model: str, text_hash: str, vector: tuple[float, ...]
    ) -> None:
        if len(vector) != EMBEDDING_DIMENSIONS:
            message = f"벡터는 {EMBEDDING_DIMENSIONS}차원이어야 합니다(받은 것: {len(vector)})."
            raise InvalidEmbedding({"vector": message})
        uow.index.put_embedding(model, text_hash, vector)
