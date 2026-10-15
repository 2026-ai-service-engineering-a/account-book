from __future__ import annotations

from api.application.dto import Outliers
from tests.api.application.use_cases.test_detect_outliers import OCTOBER


def test_nothing_found_is_still_an_answer():
    found = Outliers(OCTOBER, (), False, ())
    assert found.items == () and not found.truncated
