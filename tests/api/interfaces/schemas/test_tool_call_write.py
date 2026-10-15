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
