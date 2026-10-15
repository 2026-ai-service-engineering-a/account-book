from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.interfaces.schemas import ToolCallWrite


def test_carries_any_json_object_as_args_and_result():
    call = ToolCallWrite(call_id="c1", tool="count_frequency", args={"q": "카페"}, result=None)
    assert call.record().args == {"q": "카페"} and call.record().result is None


def test_args_must_be_an_object():
    with pytest.raises(ValidationError):
        ToolCallWrite.model_validate({"call_id": "c1", "tool": "t", "args": [1, 2]})


def test_a_gemini_call_id_with_its_thought_signature_fits():
    # 실제로 받은 모양 — 153자. 처음에 100자로 잡았다가 채팅 기록이 422로 빠졌다
    gemini = "call_91101__thought__" + "EmAKXgFpFH0TocborrMWfg8cfA7hv/5nE2viDAcIjw39V5612+" * 3
    assert len(gemini) > 150
    assert ToolCallWrite(call_id=gemini, tool="summarize_spending", args={}).call_id == gemini
