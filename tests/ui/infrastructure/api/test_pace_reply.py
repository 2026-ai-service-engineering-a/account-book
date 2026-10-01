from __future__ import annotations

from tests.ui.infrastructure.api.conftest import PACE
from ui.application.values import Money
from ui.infrastructure.api import PaceReply


def test_becomes_a_ui_series():
    series = PaceReply.model_validate(PACE).series()
    assert series.cumulative[-1] == Money(180000) and series.days_in_month == 30
