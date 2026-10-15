from __future__ import annotations

from api.application.dto import Outliers
from api.interfaces.schemas import OutliersBody
from tests.api.application.use_cases.test_detect_outliers import OCTOBER


def test_an_empty_answer_still_says_which_baseline():
    body = OutliersBody.of(Outliers(OCTOBER, (), False, ())).model_dump(mode="json")
    assert body["items"] == [] and body["skipped"] == []
    assert body["baseline_from"] == "2026-10-01T00:00:00+09:00"
