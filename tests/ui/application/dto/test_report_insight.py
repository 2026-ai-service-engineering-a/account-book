from __future__ import annotations

from ui.application.dto import ReportInsight


def test_nothing_found_is_quiet():
    assert ReportInsight().is_quiet
    assert not ReportInsight(highlights=("식비가 늘었어요.",)).is_quiet
