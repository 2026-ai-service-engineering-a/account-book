from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.interfaces.schemas import CaptureRequest

BODY = {"text": "카페 5천원", "now": "2026-10-01T09:00:00+00:00", "timezone": "Asia/Seoul"}


def test_now_is_moved_into_the_users_zone():
    local = CaptureRequest.model_validate(BODY).local_now()
    assert (local.hour, str(local.tzinfo)) == (18, "Asia/Seoul")


@pytest.mark.parametrize(
    "broken",
    [
        {"now": "2026-10-01T09:00:00"},  # naive — 기준 시각을 추측하지 않는다
        {"timezone": "Mars/Base"},
        {"text": ""},
        {"text": "가" * 2001},
    ],
)
def test_rejects(broken):
    with pytest.raises(ValidationError):
        CaptureRequest.model_validate(BODY | broken)
