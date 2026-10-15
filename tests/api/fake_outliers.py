"""이상치 집계의 가짜 — SQL(percentile_cont·round)과 같은 뜻으로 메모리에서 잰다."""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from api.application.dto import CategoryBaseline, TransactionQuery
from api.domain.entities import Transaction
from api.domain.values import CategoryId, Money


def matches(t: Transaction, query: TransactionQuery) -> bool:
    """filter_conditions와 같은 걸름."""
    return (
        (query.start is None or t.occurred_at >= query.start)
        and (query.end is None or t.occurred_at < query.end)
        and (query.direction is None or t.direction is query.direction)
        and (query.category_id is None or t.category_id == query.category_id)
        and (not query.text or query.text in t.merchant or query.text in t.memo)
    )


def baselines(
    rows: Iterable[Transaction], query: TransactionQuery, since: datetime
) -> tuple[CategoryBaseline, ...]:
    assert query.start is not None and query.direction is not None
    rows = list(rows)
    present = sorted({t.category_id for t in rows if matches(t, query)})
    out: list[CategoryBaseline] = []
    for category in present:
        same = [t for t in rows if t.category_id == category and t.direction is query.direction]
        before = [t.occurred_at for t in same if t.occurred_at < query.start]
        window = [t.amount.amount for t in same if since <= t.occurred_at < query.start]
        median = statistics.median(window) if window else 0
        mad = statistics.median([abs(a - median) for a in window]) if window else 0
        out.append(
            CategoryBaseline(
                category, _won(median), _won(mad), len(window), min(before, default=None)
            )
        )
    return tuple(out)


def above(
    rows: Iterable[Transaction],
    query: TransactionQuery,
    uppers: Mapping[CategoryId, Money],
    limit: int,
) -> tuple[Transaction, ...]:
    over = [
        t
        for t in rows
        if matches(t, query) and t.category_id in uppers and t.amount > uppers[t.category_id]
    ]
    over.sort(key=lambda t: t.id)
    over.sort(key=lambda t: t.occurred_at, reverse=True)
    over.sort(key=lambda t: t.amount.amount / uppers[t.category_id].amount, reverse=True)
    return tuple(over[:limit])


def _won(value: float) -> Money:
    """Postgres의 round()처럼 .5는 0에서 멀어지는 쪽으로."""
    return Money(int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
