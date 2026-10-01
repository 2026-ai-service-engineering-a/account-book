"""데모 데이터 — 여섯 달치 예시 거래와 예산. ui의 메모리 대역이 뜰 때마다 채우던 것을 옮겼다.

날짜를 박아 두지 않고 지금을 기준으로 만든다. 언제 넣어도 "이번 달"에 기록이 있다.
씨앗이 고정이라 같은 날 넣으면 같은 데이터가 나온다.
"""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, time, tzinfo

from sqlalchemy import Connection, exists, insert, select

from api.domain.rules.searchable_text import searchable_text, text_hash
from api.domain.values import Period

from .rows import BudgetRow, TransactionRow

_LUNCH = ("김밥천국", "한솥도시락", "본죽", "맥도날드", "서브웨이", "국밥집")
_DINNER = ("배달의민족", "교촌치킨", "이자카야", "고깃집")
_CAFE = ("스타벅스", "메가커피", "투썸플레이스", "이디야")
_LIVING = ("이마트", "쿠팡", "다이소", "올리브영")
_INCOME = {"salary", "other_income"}
# 주거는 예산을 두지 않는다. 1일에 한 번 나가는 고정비라 일할 페이스가 뜻이 없다.
_LIMITS = {"food": 300_000, "transport": 100_000, "living": 250_000}
_MONTHS = 6


def seed_demo(connection: Connection, now: datetime, zone: tzinfo) -> int:
    """거래가 하나도 없을 때만 넣는다. 넣은 거래 수 — 이미 있으면 0.

    사용자가 쓰던 가계부에 예시가 섞이면 안 된다. 그래서 "비어 있으면"이 조건이다.
    """
    if connection.execute(select(exists().select_from(TransactionRow))).scalar():
        return 0
    local_now = now.astimezone(zone)
    rng = random.Random(20260917)
    rows: list[dict[str, object]] = []
    current = Period.of(local_now.date())
    period = current
    for _ in range(_MONTHS - 1):
        period = period.previous()
    first = period
    while period <= current:
        last = local_now.day if period == current else period.days
        for day in range(1, last + 1):
            rows += _day(rng, date(period.year, period.month, day), local_now, zone)
        period = period.next()
    connection.execute(insert(TransactionRow), rows)
    # 예산은 가장 이른 달에 둔다 — 그 뒤의 달은 바뀔 때까지 같은 예산을 이어 쓴다
    connection.execute(
        insert(BudgetRow),
        [{"category_id": c, "period": str(first), "limit_amount": a} for c, a in _LIMITS.items()],
    )
    return len(rows)


def _day(rng: random.Random, day: date, now: datetime, zone: tzinfo) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add(at: time, category: str, amount: int, merchant: str, account: str = "card") -> None:
        when = datetime.combine(day, at, tzinfo=zone)
        if when > now:
            return
        source = "agent" if rng.random() < 0.35 else "manual"
        rows.append(
            {
                "id": str(uuid.UUID(int=rng.getrandbits(128), version=4)),
                "direction": "income" if category in _INCOME else "expense",
                "amount": amount,
                "occurred_at": when,
                "category_id": category,
                "account_id": account,
                "merchant": merchant,
                "memo": "",
                "source": source,
                "search_text": searchable_text(merchant, ""),
                "text_hash": text_hash(searchable_text(merchant, "")),
            }
        )

    weekday = day.weekday() < 5
    if day.day == 1:
        add(time(9), "housing", 450_000, "월세", "bank")
    if day.day == 10:
        add(time(9), "salary", 3_200_000, f"{day.month}월 급여", "bank")
    if day.day == 25:
        add(time(20), "etc", 17_000, "넷플릭스")
    if weekday and rng.random() < 0.9:
        add(time(8, 40), "transport", 1_400, "지하철")
    if weekday and rng.random() < 0.8:
        amount = rng.choice((8_000, 8_500, 9_000, 9_500, 11_000, 12_000))
        add(time(12, 30), "food", amount, rng.choice(_LUNCH))
    if rng.random() < 0.3:
        add(time(13, 10), "cafe", rng.choice((4_500, 5_000, 5_800, 6_300)), rng.choice(_CAFE))
    if day.weekday() == 5:
        add(time(16), "living", rng.randrange(30, 90) * 1_000, rng.choice(_LIVING))
    if not weekday and rng.random() < 0.5:
        add(time(19), "food", rng.randrange(20, 46) * 1_000, rng.choice(_DINNER))
    if rng.random() < 0.05:
        add(time(21), "transport", rng.randrange(8, 25) * 1_000, "카카오T", "card")
    return rows
