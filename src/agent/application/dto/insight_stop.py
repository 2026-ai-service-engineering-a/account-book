from __future__ import annotations

from enum import StrEnum


class InsightStop(StrEnum):
    """리포트 실행이 어떻게 끝났나. 감사 로그의 stop_reason이다."""

    ASSEMBLED = "assembled"  # 차트나 문장이 하나 이상 살아남았다
    DISCARDED = "discarded"  # 조립은 했지만 검증에서 전부 버렸다
    NO_BASE = "no_base"  # 고정 호출이 실패했다 — 훑지 못하고는 계획하지 않는다
    MALFORMED = "malformed"  # 모델 출력이 두 번 모양을 못 맞췄다
    WALL_CLOCK = "wall_clock"  # 벽시계 상한(10초)에 닿았다 — 늦은 리포트는 안 연다
    CACHED = "cached"  # 같은 키의 답을 캐시에서 — LLM을 부르지 않았다(agentic-reports 8장)

    @property
    def cacheable(self) -> bool:
        """같은 입력이면 같은 답일 끝만 담는다. 장애·시간 초과는 다음에 다시 해 볼 일이다."""
        return self in (InsightStop.ASSEMBLED, InsightStop.DISCARDED)
