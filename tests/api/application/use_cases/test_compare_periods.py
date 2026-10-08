from __future__ import annotations

from datetime import datetime

from api.application.use_cases import ComparePeriods
from api.domain.values import CategoryId, Money, TimeRange
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL


def month(m: int) -> TimeRange:
    return TimeRange(datetime(2026, m, 1, tzinfo=SEOUL), datetime(2026, m + 1, 1, tzinfo=SEOUL))


def test_by_category_with_change_largest_b_first():
    rows = ComparePeriods(ledger())(month(8), month(9))
    assert [(r.category.id, r.a, r.b, r.delta, r.percent) for r in rows] == [
        ("food", Money(30_000), Money(180_000), Money(150_000), 500),
        ("cafe", Money(4_000), Money(5_000), Money(1_000), 25),
    ]


def test_one_category_when_asked():
    rows = ComparePeriods(ledger())(month(8), month(9), CategoryId("cafe"))
    assert [r.category.id for r in rows] == ["cafe"]


def test_quiet_categories_drop_unless_asked_for():
    compare = ComparePeriods(ledger())
    assert compare(month(10), month(11)) == ()
    (food,) = compare(month(10), month(11), CategoryId("food"))
    assert (food.a, food.b, food.delta, food.percent) == (Money(0), Money(0), Money(0), None)


def test_unknown_category_is_empty():
    assert ComparePeriods(ledger())(month(8), month(9), CategoryId("nope")) == ()
