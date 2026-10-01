from __future__ import annotations

from collections.abc import Sequence

import litellm

from agent.application.errors import ModelUnavailable

# 가맹점명끼리의 "같은 종류인가"를 묻는다. 기본값(검색용)보다 이쪽이 카테고리를 잘 갈랐다 —
# 15개 질의 top-1 정확도 13 → 14, 자신 있게 틀린 것 1 → 0 (docs/ai/category-suggestion-rag.md 5장).
_TASK = "SEMANTIC_SIMILARITY"


class LitellmEmbedder:
    """litellm으로 임베딩한다. 반환값(`Any`)은 여기서 실수 튜플로 바꾼다."""

    def __init__(self, model: str, api_key: str, dimensions: int, timeout: float) -> None:
        self._model = model
        self._api_key = api_key
        self._dimensions = dimensions
        self._timeout = timeout

    @property
    def model(self) -> str:
        # 차원이 다르면 다른 벡터다. 모델 이름에 붙여 두면 차원을 바꿨을 때 전부 다시 색인된다.
        return f"{self._model}@{self._dimensions}"

    async def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        try:
            response = await litellm.aembedding(
                model=self._model,
                input=list(texts),
                dimensions=self._dimensions,
                task_type=_TASK,
                api_key=self._api_key,
                timeout=self._timeout,
            )
            vectors = tuple(tuple(float(x) for x in item["embedding"]) for item in response.data)
        # 제공자마다 예외가 다르다. 어느 것이든 다시 시켜도 같은 답이라 한 가지로 번역한다.
        except Exception as error:
            raise ModelUnavailable(type(error).__name__) from error
        if len(vectors) != len(texts):
            raise ModelUnavailable("벡터 수가 텍스트 수와 다르다")
        return vectors
