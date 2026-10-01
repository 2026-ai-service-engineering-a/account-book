"""벡터 이웃의 가중 투표(docs/ai/category-suggestion-rag.md 5장)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from api.domain.values import CategoryId


def vote(
    neighbors: Sequence[tuple[float, CategoryId]], temperature: float
) -> list[tuple[CategoryId, float]]:
    """이웃 (유사도, 카테고리)로 카테고리별 신뢰도를 낸다. 합이 1이고, 높은 순이다.

    유사도를 그대로 더하지 않고 1위와의 차이를 온도로 나눠 지수로 늘린다. 짧은 가맹점명의
    임베딩 유사도는 0.55~0.86에 몰려 있어서, 그대로 더하면 건수 투표와 같아지고 가장 흔한
    카테고리(식비)가 늘 이긴다. 온도가 낮을수록 가장 비슷한 이웃의 말이 무거워진다.
    """
    if not neighbors:
        return []
    best = max(similarity for similarity, _ in neighbors)
    weights: dict[CategoryId, float] = {}
    for similarity, category in neighbors:
        weight = math.exp((similarity - best) / temperature)
        weights[category] = weights.get(category, 0.0) + weight
    total = sum(weights.values())
    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    return [(category, weight / total) for category, weight in ranked]
