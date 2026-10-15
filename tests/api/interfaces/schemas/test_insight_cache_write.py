from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.interfaces.schemas import InsightCacheWrite


def test_the_body_is_an_object():
    assert InsightCacheWrite(body={"charts": []}).body == {"charts": []}
    with pytest.raises(ValidationError):
        InsightCacheWrite.model_validate({"body": [1]})
