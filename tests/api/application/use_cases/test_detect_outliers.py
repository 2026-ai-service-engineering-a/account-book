from __future__ import annotations

from datetime import datetime

from api.application.use_cases import DetectOutliers
from api.domain.entities import Transaction
from api.domain.values import (
    AccountId,
    CategoryId,
    Direction,
    Money,
    Source,
    TimeRange,
    TransactionId,
)
from tests.api.conftest import SEOUL, FakeUnitOfWork

OCTOBER = TimeRange(datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 11, 1, tzinfo=SEOUL))
# 식비의 평소(4~9월 10건): 중앙값 9,000원, MAD 400원 → 한계 max(11,076, 18,000) = 18,000원
FOOD_USUAL = (
    (4, 8000), (4, 9000), (5, 9500), (5, 8500), (6, 10000),
    (6, 9000), (7, 8800), (8, 9200), (9, 9600), (9, 8700),
)  # fmt: skip


def spend(
    n: int,
    category: str,
    amount: int,
    month: int,
    day: int = 10,
    year: int = 2026,
    merchant: str = "가게",
    direction: Direction = Direction.EXPENSE,
) -> Transaction:
    return Transaction(
        id=TransactionId(f"t{n:03d}"),
        direction=direction,
        amount=Money(amount),
        occurred_at=datetime(year, month, day, 12, tzinfo=SEOUL),
        category_id=CategoryId(category),
        account_id=AccountId("card"),
        merchant=merchant,
        memo="",
        source=Source.MANUAL,
    )


def history() -> list[Transaction]:
    """식비는 판정한다. 카페는 6월에 시작해 여섯 달이 안 된다. 생활은 기준 기간에 2건뿐이다."""
    rows = [spend(1, "food", 8200, 3, 20)]
    rows += [spend(10 + i, "food", a, m, 5 + i) for i, (m, a) in enumerate(FOOD_USUAL)]
    rows += [spend(30 + i, "cafe", a, m) for i, (m, a) in enumerate(((6, 4500), (8, 5200)))]
    rows += [spend(40, "living", 30000, 12, year=2025), spend(41, "living", 20000, 5)]
    rows += [spend(42, "living", 25000, 8)]
    return [
        *rows,
        spend(50, "food", 9500, 10, 2),  # 평소
        spend(51, "food", 18000, 10, 3),  # 한계와 같다 — 평소다
        spend(52, "food", 45000, 10, 4, merchant="한우 오마카세"),  # 2.5배
        spend(53, "food", 27000, 10, 5, merchant="편의점 회식"),  # 1.5배
        spend(54, "cafe", 30000, 10, 6),
        spend(55, "living", 90000, 10, 7),
        spend(56, "salary", 3_000_000, 10, 8, direction=Direction.INCOME),
    ]


def ledger(rows: list[Transaction] | None = None) -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    for t in history() if rows is None else rows:
        uow.transactions.add(t)
    return uow


def detect(uow: FakeUnitOfWork | None = None, **filters: object):
    return DetectOutliers(uow or ledger(), SEOUL)(OCTOBER, **filters)  # type: ignore[arg-type]


def test_picks_what_is_beyond_the_usual_range_furthest_first():
    found = detect()
    assert [t.transaction.id for t in found.items] == ["t052", "t053"]
    first = found.items[0]
    assert (first.usual_median, first.usual_upper) == (Money(9000), Money(18000))
    assert not found.truncated
    assert found.baseline == TimeRange(datetime(2026, 4, 1, tzinfo=SEOUL), OCTOBER.start)


def test_says_why_a_category_was_not_judged():
    reasons = {(s.category_id, s.reason) for s in detect().skipped}
    assert reasons == {("cafe", "short_history"), ("living", "too_few")}


def test_filters_like_the_summary_and_never_narrow_the_usual():
    # 글자 걸름은 판정할 거래만 고른다. 평소는 식비 전체로 잰다
    found = detect(text="오마카세")
    assert [t.transaction.id for t in found.items] == ["t052"] and found.skipped == ()
    only_cafe = detect(category_id=CategoryId("cafe"))
    assert only_cafe.items == () and [s.category_id for s in only_cafe.skipped] == ["cafe"]


def test_income_is_judged_only_when_asked():
    found = detect(direction=Direction.INCOME)
    assert found.items == () and [s.reason for s in found.skipped] == ["short_history"]


def test_more_than_five_is_cut_and_says_so():
    rows = history() + [spend(60 + i, "food", 40000 + i, 10, 20) for i in range(5)]
    found = detect(ledger(rows))
    assert len(found.items) == 5 and found.truncated
