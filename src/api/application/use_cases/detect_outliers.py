from __future__ import annotations

from collections.abc import Callable
from datetime import tzinfo

from api.application.dto import Outlier, Outliers, SkippedCategory, TransactionQuery
from api.application.ports import UnitOfWork
from api.domain.rules.usual_range import baseline_start, unjudged, usual_upper
from api.domain.values import CategoryId, Direction, Money, TimeRange

LIMIT = 5  # 도구 한 번에 내는 건수(ai/tools.md 4.1)


class DetectOutliers:
    """평소 범위를 벗어난 거래 — `detect_outliers` 도구의 자리(api-contract 6장).

    기준은 api가 정한다(domain/rules/usual_range). 부르는 쪽은 기간과 걸름만 넘긴다.
    걸름은 `summarize_spending`과 같고 판정할 거래를 고른다. 방향의 기본은 지출이다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], zone: tzinfo) -> None:
        self._unit_of_work = unit_of_work
        self._zone = zone

    def __call__(
        self,
        period: TimeRange,
        direction: Direction = Direction.EXPENSE,
        category_id: CategoryId | None = None,
        text: str = "",
    ) -> Outliers:
        since = baseline_start(period.start, self._zone)
        query = TransactionQuery(
            start=period.start,
            end=period.end,
            direction=direction,
            category_id=category_id,
            text=text.strip(),
        )
        medians: dict[CategoryId, Money] = {}
        uppers: dict[CategoryId, Money] = {}
        skipped: list[SkippedCategory] = []
        with self._unit_of_work() as uow:
            for usual in uow.stats.baselines(query, since):
                reason = unjudged(usual.first_at, since, usual.count)
                if reason is not None:
                    skipped.append(SkippedCategory(usual.category_id, reason))
                    continue
                medians[usual.category_id] = usual.median
                uppers[usual.category_id] = usual_upper(usual.median, usual.mad, usual.largest)
            # 하나 더 받아 본다 — 넘쳤는지를 알려야 부르는 쪽이 "이게 전부"라고 말하지 않는다
            over = uow.stats.above(query, uppers, LIMIT + 1)
        items = tuple(
            Outlier(t, medians[t.category_id], uppers[t.category_id]) for t in over[:LIMIT]
        )
        return Outliers(TimeRange(since, period.start), items, len(over) > LIMIT, tuple(skipped))
