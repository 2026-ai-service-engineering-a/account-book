from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable

WINDOW_SECONDS = 60.0


class RateLimit:
    """분당 호출 상한 — 지난 60초에 받은 호출을 센다(docs/ai/mcp.md 5장).

    루프에 빠진 외부 에이전트가 우리 api와 DB를 두드리는 것을 막는 것은 우리 몫이다.
    프로세스 하나가 클라이언트 하나라(stdio) 메모리에 센다.
    """

    def __init__(self, per_minute: int, timer: Callable[[], float]) -> None:
        if per_minute < 1:
            raise ValueError("분당 상한은 1 이상이다")
        self._limit = per_minute
        self._timer = timer  # 초 단위 단조 시계
        self._calls: deque[float] = deque()

    def take(self) -> int:
        """받으면 0. 넘었으면 다시 부를 수 있을 때까지의 초(올림) — 그 호출은 세지 않는다."""
        now = self._timer()
        while self._calls and now - self._calls[0] >= WINDOW_SECONDS:
            self._calls.popleft()
        if len(self._calls) >= self._limit:
            return max(1, math.ceil(WINDOW_SECONDS - (now - self._calls[0])))
        self._calls.append(now)
        return 0
