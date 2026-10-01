from __future__ import annotations

from datetime import datetime

import pytest

from api.application.use_cases.draft_check import check_draft
from api.domain.errors import InvalidTransaction
from api.domain.values import Direction
from tests.api.conftest import FakeCatalog, draft


def errors_of(**kwargs) -> dict[str, str]:
    with pytest.raises(InvalidTransaction) as caught:
        check_draft(draft(**kwargs), FakeCatalog())
    return caught.value.details


def test_a_good_draft_passes():
    check_draft(draft(), FakeCatalog())


def test_collects_every_problem_at_once():
    found = errors_of(amount=0, category="nope", account="nope")
    assert set(found) == {"amount", "category_id", "account_id"}


def test_category_must_match_the_direction():
    assert errors_of(category="salary")["category_id"] == "방향에 맞는 카테고리가 아닙니다."
    check_draft(draft(category="salary", direction=Direction.INCOME), FakeCatalog())


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"amount": 10_000_000_001}, "amount"),
        ({"merchant": "가" * 101}, "merchant"),
        ({"at": datetime(2026, 9, 16, 12)}, "occurred_at"),
    ],
)
def test_limits(kwargs, field):
    assert field in errors_of(**kwargs)
