from __future__ import annotations

from api.application.dto import Outlier
from api.domain.values import Money
from api.interfaces.schemas import OutlierBody
from tests.api.application.use_cases.test_detect_outliers import spend


def test_money_goes_out_as_whole_won():
    body = OutlierBody.of(Outlier(spend(1, "food", 45000, 10), Money(9000), Money(18000)))
    assert (body.transaction.amount, body.usual_median, body.usual_upper) == (45000, 9000, 18000)
