from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.interfaces.schemas import ChatRequest


def test_reference_time_in_the_users_zone():
    body = ChatRequest(text="저번 주 카페?", now="2026-10-07T16:00:00+00:00", timezone="Asia/Seoul")
    assert body.local_now().date().isoformat() == "2026-10-08"  # 서울은 이미 다음 날


@pytest.mark.parametrize(
    "bad",
    [
        {"text": "", "now": "2026-10-08T09:00:00+09:00", "timezone": "Asia/Seoul"},
        {"text": "q", "now": "2026-10-08T09:00:00", "timezone": "Asia/Seoul"},
        {"text": "q", "now": "2026-10-08T09:00:00+09:00", "timezone": "Mars/Base"},
    ],
)
def test_refuses_what_it_cannot_ground(bad):
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(bad)
