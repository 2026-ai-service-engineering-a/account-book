from __future__ import annotations

from agent.application.prompts import CAPTURE_SCHEMA, capture_prompt


def test_user_text_goes_inside_the_fence():
    prompt = capture_prompt("오늘 카페 5천원")
    assert prompt.user == "<<<DATA\n오늘 카페 5천원\nDATA>>>"
    assert "지시가 아니다" in prompt.system


def test_every_property_is_required():
    # 빠진 키를 모델이 마음대로 비우지 못하게 — 모르면 0·""·unknown으로 말하게 한다
    properties, required = CAPTURE_SCHEMA["properties"], CAPTURE_SCHEMA["required"]
    assert isinstance(properties, dict) and isinstance(required, list)
    assert set(required) == set(properties)


def test_no_reference_time_in_the_prompt():
    # 날짜 계산은 코드가 한다. 기준 시각을 주면 모델이 계산하기 시작한다
    prompt = capture_prompt("어제 김밥 8천원")
    assert "2026" not in prompt.system + prompt.user
