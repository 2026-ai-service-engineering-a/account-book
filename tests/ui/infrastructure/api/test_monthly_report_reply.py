from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.ui.infrastructure.api.conftest import MONTHLY
from ui.application.values import Money
from ui.infrastructure.api import MonthlyReportReply


def test_becomes_a_ui_report_without_adding_anything():
    report = MonthlyReportReply.model_validate(MONTHLY).report()
    assert report.totals.expense == Money(185000) and report.previous is not None
    assert (
        report.by_category[0].delta == Money(150000) and str(report.months[0].period) == "2026-08"
    )


def test_bad_period_is_refused():
    with pytest.raises((ValidationError, ValueError)):
        MonthlyReportReply.model_validate(MONTHLY | {"period": "2026-9"}).report()
