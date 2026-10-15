from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, time, tzinfo

from agent.application.dto import Insight
from agent.application.errors import LedgerUnavailable
from agent.application.ports import InsightCache, LedgerApi
from agent.application.prompts import insight_prompt_version
from agent.domain.values import TimeRange

from .build_insights import BuildInsights
from .insight_body import insight_body, insight_from_body

_log = logging.getLogger(__name__)
_BASELINE_MONTHS = 6  # detect_outliers가 평소로 보는 앞 여섯 달 — 버전도 그만큼 본다


class CachedInsights:
    """같은 달을 두 번 열면 같은 리포트가, 두 번째는 공짜로(docs/ai/agentic-reports.md 8장).

    키는 period · data_version · prompt_version · model. TTL은 없다 — 데이터가 바뀌면 키가 바뀐다.
    data_version은 리포트가 읽는 범위(그 달과 앞 여섯 달, 예산 전부)로 잰다. 오늘 커피를 넣어도
    지난달 리포트는 그대로다. 캐시는 가속기다 — 닿지 못하면 그냥 만든다(원칙 8).
    """

    def __init__(
        self, build: BuildInsights, ledger: LedgerApi, cache: InsightCache, model: str
    ) -> None:
        self._build = build
        self._ledger = ledger
        self._cache = cache
        self._model = model
        self._prompt = insight_prompt_version()

    async def __call__(self, month: date, today: date, zone: tzinfo) -> Insight:
        key = await self._key(month, zone)
        if key is not None:
            cached = await self._read(key)
            if cached is not None:
                return cached
        found = await self._build(month, today, zone)
        if key is not None and found.stop.cacheable:
            await self._write(key, found)
        return found

    async def _key(self, month: date, zone: tzinfo) -> str | None:
        try:
            version = await self._ledger.data_version(_window(month, zone))
        except LedgerUnavailable as error:
            _log.warning("insight cache skipped: %s", type(error).__name__)
            return None
        material = f"{month:%Y-%m}|{version}|{self._prompt}|{self._model}"
        return hashlib.sha256(material.encode()).hexdigest()

    async def _read(self, key: str) -> Insight | None:
        try:
            body = await self._cache.get(key)
        except LedgerUnavailable as error:
            _log.warning("insight cache read failed: %s", type(error).__name__)
            return None
        return insight_from_body(body) if body is not None else None

    async def _write(self, key: str, found: Insight) -> None:
        try:
            await self._cache.put(key, insight_body(found))
        except LedgerUnavailable as error:
            # 다음에 다시 만들 뿐이다 — 답은 이미 있다
            _log.warning("insight cache write failed: %s", type(error).__name__)


def _window(month: date, zone: tzinfo) -> TimeRange:
    """[앞 여섯 달의 1일, 다음 달 1일) — 사용자 타임존의 자정."""
    index = month.year * 12 + month.month - 1
    start_year, start_month = divmod(index - _BASELINE_MONTHS, 12)
    end_year, end_month = divmod(index + 1, 12)
    return TimeRange(
        datetime.combine(date(start_year, start_month + 1, 1), time(0), tzinfo=zone),
        datetime.combine(date(end_year, end_month + 1, 1), time(0), tzinfo=zone),
    )
