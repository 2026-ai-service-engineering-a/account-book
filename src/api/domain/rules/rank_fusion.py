"""두 검색의 순위를 하나로 — Reciprocal Rank Fusion.

키워드 점수(트라이그램 겹침)와 벡터 점수(코사인)는 단위가 달라서 더하면 뜻이 없다. 그래서
점수가 아니라 **순위**를 합친다: 목록마다 1 / (상수 + 순위)를 더한다. 두 목록에 다 높게 있으면
위로 오고, 한쪽에만 있어도 그쪽에서 높으면 남는다.
"""

from __future__ import annotations

from collections.abc import Sequence

RRF_CONSTANT = 60  # 원 논문(Cormack 등, 2009)의 값. 순위가 낮은 쪽의 무게를 눌러 준다


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], constant: int = RRF_CONSTANT
) -> list[tuple[str, float]]:
    """(식별자, 합친 점수) — 높은 순. 같으면 어느 목록에서든 더 높이 있던 쪽이 먼저다."""
    scores: dict[str, float] = {}
    best: dict[str, int] = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1 / (constant + rank)
            best[key] = min(best.get(key, rank), rank)
    return sorted(scores.items(), key=lambda item: (-item[1], best[item[0]], item[0]))
