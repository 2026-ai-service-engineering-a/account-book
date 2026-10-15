from __future__ import annotations

from api.application.dto import CategoryBaseline
from api.domain.values import CategoryId, Money


def test_a_category_that_starts_in_the_period_has_no_first_transaction():
    usual = CategoryBaseline(CategoryId("cafe"), Money(0), Money(0), Money(0), 0, None)
    assert usual.first_at is None and usual.count == 0
