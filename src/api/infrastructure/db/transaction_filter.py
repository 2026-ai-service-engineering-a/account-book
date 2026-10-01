"""거래 걸름을 SQL 조건으로. 목록과 집계가 같은 걸름을 쓴다 — 둘이 다른 거래를 세지 않게."""

from __future__ import annotations

from sqlalchemy import ColumnElement, or_

from api.application.dto import TransactionQuery

from .rows import TransactionRow


def filter_conditions(query: TransactionQuery) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if query.start is not None:
        conditions.append(TransactionRow.occurred_at >= query.start)
    if query.end is not None:
        conditions.append(TransactionRow.occurred_at < query.end)
    if query.direction is not None:
        conditions.append(TransactionRow.direction == query.direction.value)
    if query.category_id is not None:
        conditions.append(TransactionRow.category_id == query.category_id)
    if query.text:
        # %·_를 글자로 — 사용자가 친 "100%"가 와일드카드가 되지 않게
        conditions.append(
            or_(
                TransactionRow.merchant.icontains(query.text, autoescape=True),
                TransactionRow.memo.icontains(query.text, autoescape=True),
            )
        )
    return conditions
