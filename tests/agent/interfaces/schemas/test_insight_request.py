from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.interfaces.schemas import InsightRequest

NOW = {"now": "2026-10-15T09:00:00+09:00", "timezone": "Asia/Seoul"}


def test_this_month_and_earlier():
    assert InsightRequest.model_validate({"month": "2026-10", **NOW}).month == "2026-10"
    assert InsightRequest.model_validate({"month": "2025-11", **NOW}).month == "2025-11"


@pytest.mark.parametrize("month", ["2026-11", "2026-13", "2026-9", "9월"])
def test_not_a_month_or_not_yet(month):
    with pytest.raises(ValidationError):
        InsightRequest.model_validate({"month": month, **NOW})


def test_the_month_turns_in_the_users_zone():
    # UTC로는 10월 31일 16시지만 서울은 11월 1일이다 — 11월이 이미 왔다
    late = {"now": "2026-10-31T16:00:00+00:00", "timezone": "Asia/Seoul"}
    assert InsightRequest.model_validate({"month": "2026-11", **late}).month == "2026-11"
