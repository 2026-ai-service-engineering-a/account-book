"""대역 저장소를 채우는 예시 데이터. 여섯 달치, 오늘 이 시각까지.

날짜를 박아 두지 않고 지금을 기준으로 만든다. 언제 띄워도 "이번 달"에 기록이 있다.
씨앗이 고정이라 같은 날 띄우면 같은 데이터가 나온다.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time

from ui.application.dto import Direction, Period, Source, Transaction
from ui.application.values import AccountId, CategoryId, Money

from .memory_store import MemoryStore

_LUNCH = ("김밥천국", "한솥도시락", "본죽", "맥도날드", "서브웨이", "국밥집")
_DINNER = ("배달의민족", "교촌치킨", "이자카야", "고깃집")
_CAFE = ("스타벅스", "메가커피", "투썸플레이스", "이디야")
_LIVING = ("이마트", "쿠팡", "다이소", "올리브영")
# 주거는 예산을 두지 않는다. 1일에 한 번 나가는 고정비라 일할 페이스가 뜻이 없다.
_LIMITS = {
    CategoryId("food"): Money(300_000),
    CategoryId("transport"): Money(100_000),
    CategoryId("living"): Money(250_000),
}


def seed_demo(store: MemoryStore, now: datetime) -> None:
    rng = random.Random(20260917)
    current = Period.of(now.date())
    period = current
    for _ in range(5):
        period = period.previous()
    while period <= current:
        last = now.day if period == current else period.days
        for day in range(1, last + 1):
            _seed_day(store, rng, date(period.year, period.month, day), now)
        period = period.next()
    store.limits.update(_LIMITS)


def _seed_day(store: MemoryStore, rng: random.Random, day: date, now: datetime) -> None:
    def add(at: time, category: str, amount: int, merchant: str, account: str = "card") -> None:
        when = datetime.combine(day, at, tzinfo=store.zone)
        if when > now:
            return
        income = store.categories[CategoryId(category)].direction == Direction.INCOME
        source = Source.AGENT if rng.random() < 0.35 else Source.MANUAL
        tx = Transaction(
            id=store.next_id(),
            direction=Direction.INCOME if income else Direction.EXPENSE,
            amount=Money(amount),
            occurred_at=when,
            category_id=CategoryId(category),
            account_id=AccountId(account),
            merchant=merchant,
            memo="",
            source=source,
        )
        store.transactions[tx.id] = tx

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
