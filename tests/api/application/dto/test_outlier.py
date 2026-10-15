from __future__ import annotations

from api.application.dto import Outlier
from api.domain.values import Money
from tests.api.application.use_cases.test_detect_outliers import spend


def test_keeps_the_usual_next_to_the_transaction():
    found = Outlier(spend(1, "food", 45000, 10), Money(9000), Money(18000))
    assert found.transaction.amount > found.usual_upper > found.usual_median
